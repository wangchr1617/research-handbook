# 技能与 MCP 工具的安装及使用技巧

**适用环境：Codex、Claude Code；命令在相应客户端所在的本机终端执行。**

Skills 和 MCP 经常一起出现，但解决的问题不同：技能告诉助手“这类任务怎样做”，MCP 为助手提供“可以调用什么工具”。插件则可能把两者打包分发。

## 开始前

先安装一个宿主客户端并跑通普通对话：[Codex](Codex配置与使用技巧.md)、[Claude Code（Mac）](VSCode、ClaudeCode与CC%20Switch配置（Mac）.md)或 [Claude Code（Windows / WSL）](VSCode、ClaudeCode与CC%20Switch配置（Windows）.md)。技能和 MCP 配置需要安装到实际运行这个客户端的系统里。

准备下载技能时，可先浏览 [OpenAI 官方技能仓库](https://github.com/openai/skills)和 [Anthropic 官方技能仓库](https://github.com/anthropics/skills)。GitHub 页面点击绿色 `Code` → `Download ZIP`，解压后只取目标技能的完整目录；也可用 Git 克隆。先读目录中的 `SKILL.md`、许可和依赖，再按下一节放到客户端扫描的位置。

远程 MCP 不一定要安装 Node.js；本地服务器只有明确要求 Node.js、Python 或 uv 时才装对应运行时，下载入口见 [Node.js 官网](https://nodejs.org/en/download)和 [pip 与 uv](pip与uv安装与使用.md)。

## 一、先决定需要什么

| 需求 | 适合的方式 |
| --- | --- |
| 按固定规范检查输入、写报告 | Skill，通常包含 SKILL.md 和参考资料 |
| 搜索外部资料、访问授权的数据源 | MCP 或客户端支持的连接器 |
| 给团队分发一组技能与工具配置 | 对应客户端支持的插件 |

安装了绘图技能，并不等于 Python 环境已有 matplotlib；注册了一个 MCP 地址，也不等于服务器已启动或授权完成。

## 二、安装技能

先查看技能源码、许可、依赖和适用客户端。一个典型目录如下：

```text
check-inputs/
├── SKILL.md
├── scripts/
└── references/
```

本地技能的常用位置：

| 客户端 | 当前项目 | 当前用户 |
| --- | --- | --- |
| Codex | `.agents/skills/技能目录/` | `~/.agents/skills/技能目录/` |
| Claude Code | `.claude/skills/技能目录/` | `~/.claude/skills/技能目录/` |

复制完整目录，保证 `SKILL.md` 直接位于技能目录中，避免多套一层仓库文件夹。

不同客户端的专用字段、工具名和调用命令仍可能需要调整，不能仅靠复制宣称完全兼容。

Codex 可通过 `$skill-installer` 安装受支持的技能；安装后用 `/skills` 或 `$技能名` 查看、选择。若未出现，检查路径和元数据，必要时重启。详见 [OpenAI 技能文档](https://developers.openai.com/codex/skills/)。

Claude Code 项目技能可在对话中用 `/技能名` 调用；发现和调用条件受技能配置影响，详见 [Claude Code 技能文档](https://code.claude.com/docs/en/skills)。`find-skills` 等名称只有安装对应技能后才可用，不是所有客户端内置命令。

## 三、写一个最小技能

以 Codex 项目技能为例，在项目根目录执行：

```bash
mkdir -p .agents/skills/check-inputs
```

用 VSCode 新建 `.agents/skills/check-inputs/SKILL.md`，粘贴下面内容并保存。Claude Code 对应目录改为 `.claude/skills/check-inputs/`。文件名必须是 `SKILL.md`，不是 `SKILL.md.txt`。

下面是 `SKILL.md` 示例：

```markdown
---
name: check-inputs
description: 检查当前目录的科研计算输入文件、单位和配套作业脚本；不提交计算。
---

1. 读取项目约定和输入文件，列出计算软件、任务与单位。
2. 检查所需文件是否齐全，标出相互矛盾的参数。
3. 给出文件位置和修改建议；不自动覆盖原始输入或提交作业。
```

先在测试目录调用，确认报告能指出实际问题。后续再补脚本、参考资料和输出模板，避免一开始就写成难以维护的大文档。

## 四、安装一个远程 MCP

以 OpenAI 官方文档服务器为例，两种客户端分别配置，不需要同时执行。

Codex：

```bash
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
codex mcp list
```

Claude Code（当前用户范围）：

```bash
claude mcp add --transport http --scope user openaiDeveloperDocs https://developers.openai.com/mcp
claude mcp list
```

进入新会话后，请助手“使用 OpenAI 文档工具查询一个 Codex 配置项并给出来源”，检查是否实际调用工具及返回对应文档。注册步骤见 [官方 Docs MCP 指南](https://developers.openai.com/learn/docs-mcp)。

## 五、本地 MCP 与配置范围

本地 MCP 通常由客户端通过 stdio 启动子进程。服务器自己的安装说明会给出 `command`、`args` 和所需环境变量；先确认 Node.js / Python / 可执行文件能在客户端所在环境运行。

```bash
command -v node
command -v python
```

从 Dock 打开的应用可能使用不同 PATH。必要时在 MCP 配置中填写已确认的可执行文件绝对路径。Windows、WSL、Mac 和远端 Linux 的安装目录不能互相照搬。

Claude Code 的 project scope 配置可写入 `.mcp.json`；user scope 供个人跨项目使用。Codex 的用户级 MCP 配置可位于 `~/.codex/config.toml`。具体作用域、OAuth 登录和本地服务器参数见 [Claude MCP 文档](https://code.claude.com/docs/en/mcp)及各客户端帮助。

共享配置只放服务地址和必要参数，密钥由环境变量或客户端授权提供。`npx`、`uvx` 等启动器可能在首次运行时下载并执行代码，要先核对包的来源与版本。

## 六、排错与维护

| 问题 | 检查顺序 |
| --- | --- |
| 技能找不到 | 目录 → SKILL.md → name / description → 客户端刷新 |
| 技能出现但没触发 | 描述是否匹配任务，尝试显式调用 |
| MCP 注册但无法连接 | 地址 / 启动命令 → 依赖 → 代理 → 授权 → 服务日志 |
| 连通但缺少目标工具 | 服务器实际提供的工具、账号权限、客户端限制 |
| 修改后仍用旧配置 | 新开会话，检查是否有同名的项目 / 用户配置 |

先装一个、验证一个，再逐步增加。停用时从对应客户端移除注册，技能则移出扫描目录；不要把删除本地配置当作已撤销远端账号授权。
