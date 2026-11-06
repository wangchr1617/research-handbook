# 科研笔记检查

适用环境：macOS、Linux、Windows；Node.js 22 或更新版本。

组合 `markdownlint` 与 `lint-md`，检查 Markdown 结构和中文排版。工具只报告问题，不改写文件；文字逻辑、技术含义和行文建议由审阅者判断。

## 安装与运行

在仓库根目录执行，依赖仅安装到本项目：

```bash
npm ci --prefix scripts/note-audit --ignore-scripts --no-audit --no-fund
node scripts/note-audit/check.mjs
node scripts/note-audit/check.mjs notes/材料应用/README.md
node scripts/note-audit/check.mjs notes/CP2K getting-started/git
```

不传路径时检查 `notes` 和 `getting-started` 下的 Markdown。传入文件或目录时只检查指定范围，可用 `--json` 输出结构化诊断。本地文件、图片及 HTML 链接会逐段检查目标路径及大小写是否匹配；不联网检查外部地址，也不校验跨文件标题锚点。错误使退出码为 1，只有建议时退出码为 0；参数或检查过程执行失败时退出码为 2。

## 规则与审阅

固定依赖版本记录在 `package-lock.json`，规则在 `rules.json`。`markdownlint` 负责标题层级、空行、代码块语言和表格等结构；`lint-md` 补充中文与英文、数字的间距及标点建议。代码块、行内代码、公式和链接目标不参与中文正文排版检查。`CCSD(T)`、`SO(3)`、`Al(111)` 等含括号的技术记号保留半角写法。

规则集不限制正文行长、不强制统一章节模板，也不按关键词自动删除行文。先处理结构错误，再判断建议是否适合当前上下文；公式、单位、命令与第三方原文以技术准确性为准。

检查工具本身的测试可用 `npm test --prefix scripts/note-audit` 运行，覆盖代码与公式保护、结构诊断、本地链接、只读行为和退出状态。

AI 编写或润色时，可参考根目录 `AGENTS.md` 的写作约定，再结合检查结果通读正文。个人安装的审阅技能可辅助行文判断，检查工具本身可独立运行。
