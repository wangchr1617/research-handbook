import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { checkText, checkLocalLinks, proseForLint } from './check.mjs';

test('检查标题、列表与代码围栏的结构问题', () => {
  const result = checkText('# 标题\n### 步骤\n正文\n- 项目\n```\nvalue\n```\n');
  for (const rule of ['MD001', 'MD022', 'MD031', 'MD032', 'MD040']) {
    assert.ok(result.some(d => d.rule === rule), rule);
  }
});

test('代码与科学记号不触发正文排版，正文问题保留准确位置', () => {
  const text = '# 标题\n\n```text\n中文English\t123\n```\n\n`中文English`，`call(x)`，$E(x)=1$，CCSD(T)，Al(111)。\n\n中文English\n';
  const result = checkText(text);
  assert.equal(result.filter(d => d.severity === 'error').length, 0);
  assert.deepEqual(result.map(d => [d.rule, d.line]), [['space-around-alphabet', 9]]);
  assert.equal(proseForLint(text).length, text.length);
  assert.equal(proseForLint(text).split('\n').length, text.split('\n').length);
});

test('检查模式不修改源码，标点与中英文建议不变成错误', () => {
  const text = '# 标题\n\n中文English,示例.\n';
  const snapshot = text;
  const result = checkText(text);
  assert.equal(text, snapshot);
  assert.ok(result.some(d => d.rule === 'no-half-width-punctuation'));
  assert.ok(result.every(d => d.severity === 'warning'));
});

test('含竖线的表格命令正确保留单元格', () => {
  const text = '# 标题\n\n| 命令 | 说明 |\n| --- | --- |\n| `rg "ERROR\\|run_id" log` | 搜索 |\n';
  assert.equal(checkText(text).filter(d => d.rule === 'MD056').length, 0);
});

test('本地链接支持中文、转义空格和HTML图片，不请求远程链接', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'note-audit-'));
  try {
    fs.writeFileSync(path.join(dir, '中文 空格.md'), '# 标题\n');
    fs.writeFileSync(path.join(dir, 'figure.png'), 'fixture');
    const text = '[正常](中文%20空格.md#段落)\n[外部](https://example.com/a)\n<img src="figure.png">\n[丢失](missing.md)\n';
    const result = checkLocalLinks(text, path.join(dir, 'note.md'));
    assert.equal(result.length, 1);
    assert.equal(result[0].detail, 'missing.md');
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('命令行错误状态与只读执行', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'note-audit-cli-'));
  try {
    const file = path.join(dir, 'note.md');
    const run = (...args) => spawnSync(process.execPath, [path.join(import.meta.dirname, 'check.mjs'), ...args], { encoding: 'utf8' });
    const text = '# 标题\n\n中文English\n';
    fs.writeFileSync(file, text);
    const ok = run('--json', file);
    assert.equal(ok.status, 0);
    assert.equal(JSON.parse(ok.stdout).warnings, 1);
    assert.equal(fs.readFileSync(file, 'utf8'), text);
    fs.writeFileSync(file, '# 标题\n### 小节\n');
    assert.equal(run(file).status, 1);
    assert.equal(run(path.join(dir, 'missing.md')).status, 2);
    assert.equal(run('--fix', file).status, 2);
    assert.equal(run(dir).status, 1);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('新检出未安装依赖时给出明确安装入口', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'note-audit-deps-'));
  try {
    const entry = path.join(dir, 'check.mjs');
    fs.copyFileSync(path.join(import.meta.dirname, 'check.mjs'), entry);
    const result = spawnSync(process.execPath, [entry], { encoding: 'utf8' });
    assert.equal(result.status, 2);
    assert.match(result.stderr, /npm ci --prefix scripts\/note-audit/);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('大小写不匹配和目录大小写错误均作为断链报告', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'note-audit-case-'));
  try {
    fs.mkdirSync(path.join(dir, 'VASP'));
    fs.writeFileSync(path.join(dir, 'VASP', 'README.md'), '# VASP\n');
    const file = path.join(dir, 'note.md');
    const result = checkLocalLinks('[正常](VASP/README.md)\n[目录错误](vasp/README.md)\n[文件错误](VASP/readme.md)\n', file);
    assert.deepEqual(result.map(d => d.detail), ['vasp/README.md', 'VASP/readme.md']);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});
