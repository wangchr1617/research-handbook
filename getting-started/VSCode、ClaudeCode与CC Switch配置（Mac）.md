# VSCode、Claude Code 与 CC Switch 配置（Mac）

**适用环境：macOS，本机开发；Remote - SSH 对应远端 Linux。**

先把 VSCode 和 Claude Code 分别跑通，再用 CC Switch 管理供应商配置。这样遇到问题时，比较容易知道卡在哪一步。

## 开始前

先在苹果菜单 → 关于本机确认芯片，再按 [Mac 新生入门](新生入门（Mac）.md#二安装常用工具)安装 Apple 命令行工具和 Homebrew，直到 `brew --version` 能返回版本。按 `Cmd+空格` 搜索“终端”，下面的安装命令在本机终端执行。

本篇要准备三样：VSCode 编辑器、Claude Code 客户端，以及模型服务账号。CC Switch 只是配置管理工具，安装它不会附送 API 额度。没有模型账号时，按第二节选官方登录路线，或按第三节开通兼容 API 服务。

## 一、安装 VSCode

从 [VSCode 官网](https://code.visualstudio.com/docs/setup/mac)下载对应芯片的版本，拖入“应用程序”。打开后按 `Cmd+Shift+P`，执行 `Shell Command: Install 'code' command in PATH`，重新打开终端：

```bash
mkdir -p "$HOME/projects/hello-ai"
cd "$HOME/projects/hello-ai"
code .
```

扩展商店按需安装中文语言包、Python、Jupyter、Remote - SSH 和 Anthropic 官方 Claude Code 扩展。Mac 本机不需要 Remote - WSL。

## 二、安装 Claude Code

已有 Homebrew 时，在 Mac 终端执行：

```bash
brew install --cask claude-code
claude --version
claude doctor
```

安装方式以 [Claude Code 官方说明](https://code.claude.com/docs/en/setup)为准。Homebrew 安装由 `brew upgrade --cask claude-code` 更新，不要再叠加 npm 全局安装，以免 PATH 中出现多个版本。

第一次使用可以沿用第一节创建的演示目录：

```bash
cd "$HOME/projects/hello-ai"
claude
```

选择官方登录时，按终端提示打开浏览器，登录或注册 [Claude 账号](https://claude.ai/)，完成授权。可用账号和订阅要求见 [官方快速开始](https://code.claude.com/docs/en/quickstart)；不要把普通聊天账号能够登录当作 CLI 已有额度。

选择 API 路线时，先在服务商后台开通 API、确认计费并创建 Key，再进入下一节配置。先让它解释当前目录，再尝试修改一个小文件。

## 三、安装并配置 CC Switch

[CC Switch](https://github.com/farion1231/cc-switch)是独立的配置管理工具，不负责提供模型服务。可从 [官方 Releases](https://github.com/farion1231/cc-switch/releases) 的 Assets 下载 macOS 安装包并安装，或执行：

```bash
brew install --cask cc-switch
```

没有 API Key 时，可先从 [Anthropic API 平台](https://platform.claude.com/)注册、开通计费并创建 Key；第三方路线可参考 [DeepSeek 开放平台](https://platform.deepseek.com/)及其 [Anthropic 兼容接口说明](https://api-docs.deepseek.com/guides/anthropic_api/)。API 额度与聊天订阅分别管理，开通前确认自己购买的是哪一种。

打开 CC Switch，先导入或备份现有配置，然后在 **Claude Code** 对应页面添加供应商，填写服务商提供的 Anthropic 兼容地址、API Key 和模型映射。以 DeepSeek 为例，地址为 `https://api.deepseek.com/anthropic`，Key 从自己的开放平台账号创建，模型名按当前接口文档选择。普通 OpenAI 兼容地址不一定能直接用于 Claude Code。

选择并启用供应商后，退出旧的 Claude Code 会话，再从项目目录启动新会话。检查供应商、模型名称和一次最小请求的结果；切换成功的判据是请求实际返回，不只是界面显示“已启用”。

> **ps**：如果 CC Switch 开启了本地代理接管，Claude Code 配置可能指向本机代理地址。退出 CC Switch 前先退出接管或恢复直连配置，否则 Claude Code 可能找不到服务。

## 四、让扩展和终端使用同一份配置

默认先使用同一 macOS 用户下的 `~/.claude/` 配置。不要一边让 CC Switch 管理配置，一边在多个 shell 文件中设置另一套 `ANTHROPIC_*` 变量。

```bash
command -v claude
claude --version
```

如果终端成功而扩展失败，在 VSCode 的本机终端重复测试，然后重新加载窗口。检查扩展运行在哪个环境、是否设置了自定义 `CLAUDE_CONFIG_DIR`、是否有旧环境变量覆盖配置。具体扩展设置见 [官方 VSCode 文档](https://code.claude.com/docs/en/vs-code)。

Remote - SSH 窗口的终端运行在集群，Mac 上的 CC Switch 不会自动修改远端配置。需要 AI 协助集群计算时，可以采用[本机 AI → SSH → PBS](Codex连接科研集群（macOS）.md)，把模型调用留在本机。

## 五、日常使用

以修改一个后处理脚本为例，先告诉 Claude Code 输入文件、单位、预期输出和不能改动的计算方案，再让它读相关文件、提出修改并检查差异。完成后在 VSCode 的源代码管理面板查看改动，运行一个小数据测试。

项目约定放 `CLAUDE.md`，可共享的技能放项目 `.claude/skills/`，凭据留在本机配置。Skills 与 MCP 的区别和安装方法见 [技能与 MCP 工具](技能与MCP工具的安装及使用技巧.md)。

需要代理时按 [DOVE 配置](DOVE加速器配置与使用技巧.md)检查网络。不要把 API Key、CC Switch 数据库或含密钥的配置截图提交到仓库。
