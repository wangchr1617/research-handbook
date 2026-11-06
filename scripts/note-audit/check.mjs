#!/usr/bin/env node
// 检查科研 Markdown；用法：node scripts/note-audit/check.mjs [--json] [文件或目录 ...]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
let lint, lintMarkdown, chineseRules, parseMd;
try {
  [{ lint }, { lintMarkdown }, chineseRules, { parseMd }] = await Promise.all([
    import('markdownlint/sync'), import('@lint-md/core'),
    import('@lint-md/core/lib/rules/index'), import('@lint-md/parser'),
  ]);
} catch (error) {
  console.error(`无法加载笔记检查依赖：${error.message}\n请在仓库根目录执行 npm ci --prefix scripts/note-audit --ignore-scripts --no-audit --no-fund`);
  process.exit(2);
}

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const rules = JSON.parse(fs.readFileSync(path.join(here, 'rules.json'), 'utf8'));
const chineseConfig = {
  ...Object.fromEntries(Object.values(chineseRules).filter(rule => rule?.meta?.name).map(rule => [rule.meta.name, 0])),
  ...rules.lintMd,
};

// 遮盖公式与含括号的技术记号，保留 UTF-16 偏移，使诊断位置仍对应原文。
// fenced code 和 inline code 由 Markdown 解析器处理。
export function proseForLint(text) {
  const spans = [];
  const walk = node => {
    const start = node.position?.start.offset;
    const end = node.position?.end.offset;
    if (['math', 'inlineMath'].includes(node.type)) spans.push([start, end]);
    else if (node.type === 'text') {
      // 半角括号是这些技术记号的一部分；仅处理正文文本，不进入代码节点。
      const raw = text.slice(start, end);
      const pattern = /\b[A-Za-z][A-Za-z0-9_+\/-]*(?:\([A-Za-z0-9_,+\/-]+\))+|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]/g;
      for (const match of raw.matchAll(pattern)) spans.push([start + match.index, start + match.index + match[0].length]);
    }
    for (const child of node.children ?? []) walk(child);
  };
  walk(parseMd(text));
  let result = text;
  for (const [start, end] of spans.sort((a, b) => b[0] - a[0])) {
    result = result.slice(0, start) + text.slice(start, end).replace(/[^\r\n]/g, ' ') + result.slice(end);
  }
  return result;
}

export function checkText(text, name = 'note.md') {
  const diagnostics = [];
  const result = lint({ strings: { [name]: text }, config: rules.markdownlint });
  for (const d of result[name]) {
    diagnostics.push({ file: name, line: d.lineNumber, column: d.errorRange?.[0] ?? 1,
      severity: 'error', rule: d.ruleNames[0], message: d.ruleDescription,
      detail: d.errorDetail ?? d.errorContext ?? null });
  }
  const chinese = lintMarkdown(proseForLint(text), chineseConfig, false, { ruleErrorPolicy: 'strict' });
  if (!chinese.complete || chinese.executionErrors.length) {
    throw new Error(`${name}: lint-md 检查不完整`);
  }
  for (const d of chinese.diagnostics) {
    diagnostics.push({ file: name, line: d.line, column: d.column,
      severity: d.severity === 2 ? 'error' : 'warning', rule: d.ruleId, message: d.message });
  }
  return diagnostics.sort((a, b) => a.line - b.line || a.column - b.column || a.rule.localeCompare(b.rule));
}

export function checkLocalLinks(text, file) {
  const diagnostics = [];
  // 逐段核对目录项，避免 macOS 的大小写宽容掩盖 GitHub / Linux 上的断链。
  const exactPath = target => {
    const resolved = path.resolve(target);
    let cursor = path.parse(resolved).root;
    for (const part of resolved.slice(cursor.length).split(path.sep).filter(Boolean)) {
      if (!fs.existsSync(cursor) || !fs.statSync(cursor).isDirectory()) return false;
      if (!fs.readdirSync(cursor).includes(part)) return false;
      cursor = path.join(cursor, part);
    }
    return true;
  };
  const check = (url, line) => {
    if (/^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(url)) return;
    let target = url.split('#')[0].split('?')[0];
    if (!target) return;
    try { target = decodeURIComponent(target); } catch { /* 非法转义也按原路径检查。 */ }
    if (!exactPath(path.resolve(path.dirname(file), target))) {
      diagnostics.push({ file: path.relative(root, file), line, column: 1,
        severity: 'error', rule: 'LINK_MISSING', message: '本地链接目标不存在或路径大小写不匹配', detail: url });
    }
  };
  const walk = node => {
    if (['link', 'image', 'definition'].includes(node.type)) check(node.url, node.position.start.line);
    if (node.type === 'html') {
      for (const match of node.value.matchAll(/(?:src|href)\s*=\s*["']([^"']+)["']/g)) check(match[1], node.position.start.line);
    }
    for (const child of node.children ?? []) walk(child);
  };
  walk(parseMd(text));
  return diagnostics;
}

function collect(target, files) {
  const stat = fs.lstatSync(target);
  if (stat.isSymbolicLink()) throw new Error(`不检查符号链接：${target}`);
  if (stat.isDirectory()) {
    for (const entry of fs.readdirSync(target).sort()) {
      if (entry.startsWith('.') || ['node_modules', '_validation_runs', 'assets'].includes(entry)) continue;
      collect(path.join(target, entry), files);
    }
  } else if (stat.isFile() && target.endsWith('.md')) {
    files.add(target);
  }
}

export function main(args) {
  const json = args.includes('--json');
  if (args.some(a => a.startsWith('--') && a !== '--json')) throw new Error('仅支持 --json 和 Markdown 文件或目录路径');
  const targets = args.filter(a => a !== '--json');
  const files = new Set();
  for (const target of targets.length ? targets : [path.join(root, 'notes'), path.join(root, 'getting-started')]) {
    collect(path.resolve(target), files);
  }
  if (!files.size) throw new Error('指定范围内没有 Markdown 文件');
  const diagnostics = [...files].sort().flatMap(file => {
    const text = fs.readFileSync(file, 'utf8');
    return [...checkText(text, path.relative(root, file)), ...checkLocalLinks(text, file)];
  });
  const errors = diagnostics.filter(d => d.severity === 'error').length;
  const warnings = diagnostics.length - errors;
  const report = { files: files.size, errors, warnings, diagnostics };
  if (json) console.log(JSON.stringify(report, null, 2));
  else {
    for (const d of diagnostics) console.log(`${d.file}:${d.line}:${d.column} ${d.severity} ${d.rule} ${d.message}${d.detail ? ` (${d.detail})` : ''}`);
    console.log(`检查 ${files.size} 份 Markdown：${errors} 个错误，${warnings} 条建议。`);
  }
  return errors ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { process.exitCode = main(process.argv.slice(2)); }
  catch (error) { console.error(`笔记检查失败：${error.message}`); process.exitCode = 2; }
}
