# VSCode + WSL + Claude Code 开发环境配置

**适用环境：Windows 11 + WSL 2（Ubuntu）。**

在 Windows 中安装 WSL 和 VSCode，再配置 Claude Code，组成 AI 辅助开发环境。各步骤注明在 Windows 还是 WSL 中执行。

---

## 开始前

先准备 Windows 管理员权限以安装 WSL，模型客户端日常运行使用普通用户。网络准备见 [DOVE 注册与安装](DOVE加速器配置与使用技巧.md#一注册购买和安装)；下面历史 Clash 配置仅用于已经在用 Clash 的读者，不要求新生另外寻找同名客户端。

Claude Code 安装后仍需模型账号。官方路线从 [Claude](https://claude.ai/)注册并按 [快速开始](https://code.claude.com/docs/en/quickstart)登录；API 路线从 [Anthropic 平台](https://platform.claude.com/)或 [DeepSeek 开放平台](https://platform.deepseek.com/)开通计费、创建 Key。CC Switch 不提供额度。

## 环境信息

| 项目 | 值 |
|---|---|
| 操作系统 | Windows 11 + WSL 2 (Ubuntu) |
| Node.js | v22.22.0（通过 nvm 管理） |
| Claude Code | VSCode 扩展 + npm 全局安装 |
| ccswitch | CC-Switch-v3.16.2（Windows MSI 安装） |
| API 后端 | DeepSeek（`api.deepseek.com`） |
| 代理 | Clash（端口 7890） |

---

## 一、Windows 中安装 VSCode 和 WSL

### 1. 安装 VSCode

访问 [VSCode 官网](https://code.visualstudio.com/) 下载安装包，安装时勾选 **"添加到 PATH"**，以便在终端中直接使用 `code` 命令。

### 2. 安装 WSL 2

WSL 2 的安装详见 [WSL 及 Docker 安装](WSL与Docker安装使用（Windows）.md)，此处仅列关键步骤：

1. 控制面板 → 启用或关闭 Windows 功能 → 勾选 **Hyper-V**、**适用于 Linux 的 Windows 子系统**、**虚拟机平台**
2. 管理员 PowerShell：`wsl --update` → `wsl --install`
3. 重启电脑，WSL 终端中设置用户名和密码

安装完成后用 `wsl -l -v` 确认版本为 WSL 2：

```text
C:\Users\xxx> wsl -l -v
  NAME      STATE           VERSION
* Ubuntu    Running         2
```

---

## 二、Windows 中 Clash 的代理设置

WSL 中的很多操作（如 npm 安装、git clone）需要科学上网。本节说明 Windows 端 Clash 的配置要点。

### 1. 开启 Clash 并允许局域网

- 启动 Clash，勾选 **"允许局域网"（Allow LAN）**
- 查看端口号：默认 **7890**（HTTP）和 **7891**（SOCKS5）

### 2. 获取宿主机 IP

在 Windows 的 cmd 或 PowerShell 中运行 `ipconfig`，找到 **vEthernet (WSL)** 适配器的 IPv4 地址，通常以 `172.` 开头，例如 `172.31.0.1`。

> 如果 WSL 网络模式为 **Mirrored**（WSL Settings → 网络 → 网络模式），则宿主机 IP 可以直接使用 `127.0.0.1`（即 localhost），无需查找 vEthernet 地址。

### 3. 检查 WSL 网络

先确认 WSL 的网络模式、宿主机代理监听和防火墙规则，不需要为了代理默认把 DNS 开放到 `0.0.0.0:53`。HTTP / SOCKS 代理与 DNS 监听是不同配置，相关排查见 [DOVE 配置](DOVE加速器配置与使用技巧.md)。

---

## 三、WSL 中配置代理

在 `~/.bashrc` 末尾添加 `proxy_on` 和 `proxy_off` 函数，方便随时开关代理：

```bash
proxy_on() {
  HOST_IP="127.0.0.1"
  export http_proxy="http://$HOST_IP:7890"
  export https_proxy="http://$HOST_IP:7890"
  git config --global http.proxy "http://$HOST_IP:7890"
  git config --global https.proxy "http://$HOST_IP:7890"
  echo "Proxy ON: $HOST_IP:7890"
}

proxy_off() {
  unset http_proxy https_proxy
  git config --global --unset http.proxy
  git config --global --unset https.proxy
  echo "Proxy OFF"
}
```

保存后 `source ~/.bashrc` 生效。使用时：

```bash
proxy_on    # 开启代理（安装软件、git clone 前）
proxy_off   # 关闭代理（日常使用、连接集群时）
```

> **注意**：`HOST_IP` 根据你的 WSL 网络模式填写。Mirrored 模式用 `127.0.0.1`，NAT 模式用 vEthernet 的 `172.x.x.x` 地址。

---

## 四、VSCode 安装插件及连接 WSL

### 1. 推荐插件

在 VSCode 扩展商店（`Ctrl+Shift+X`）搜索并安装：

**基础必备：**

| 插件 | 用途 |
|---|---|
| **Chinese (Simplified) Language Pack** (`ms-ceintl.vscode-language-pack-zh-hans`) | 中文界面汉化 |
| **Remote - WSL** (`ms-vscode-remote.remote-wsl`) | 连接 WSL 子系统 |
| **Remote - SSH** (`ms-vscode-remote.remote-ssh`) | 远程连接集群/服务器 |

**Git 与协作：**

| 插件 | 用途 |
|---|---|
| **GitLens** (`eamodio.gitlens`) | Git 增强：行级 blame、历史对比、代码作者追踪 |
| **Git Graph** (`mhutchie.git-graph`) | Git 提交历史可视化 |

**AI 辅助：**

| 插件 | 用途 |
|---|---|
| **Claude Code**（Anthropic 官方扩展） | AI 辅助编程 |

**编辑增强：**

| 插件 | 用途 |
|---|---|
| **Markdown All in One** (`yzhang.markdown-all-in-one`) | Markdown 编辑增强（快捷键、目录生成、预览） |
| **Markdown Preview Mermaid Support** (`bierner.markdown-mermaid`) | 在 Markdown 预览中渲染 Mermaid 图表 |
| **Path Intellisense** (`christian-kohler.path-intellisense`) | 文件路径自动补全 |
| **Todo Tree** (`gruntfuggly.todo-tree`) | 汇总并高亮代码中的 TODO/FIXME 标记 |

### 2. 连接 WSL

三种方式任选：

- **方式一**：WSL 终端中进入项目目录，输入 `code .`，VSCode 会自动以 Remote-WSL 模式打开
- **方式二**：VSCode 左下角点击绿色 `><` 图标，选择 **"连接到 WSL"**
- **方式三**：`Ctrl+Shift+P` → 输入 `WSL` → 选择 **"Remote-WSL: New Window"**

连接成功后左下角显示 **"WSL: Ubuntu"**，终端自动切换为 WSL 的 bash。

---

## 五、WSL 中安装开发工具

> 以下操作均在 WSL 终端中执行。如果安装过程中卡住，先执行 `proxy_on` 开启代理。

### 1. 安装 nvm 和 Node.js

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc

# 安装 Node.js LTS 版本
nvm install 22
nvm use 22
nvm alias default 22

# 验证
node --version   # v22.x.x
npm --version    # 10.x.x
```

### 2. 安装 Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

安装完成后 `claude` 命令即可在终端中使用。同时建议在 VSCode 扩展商店安装 Claude Code 插件，获得更好的编辑体验。

### 3. 安装 CC Switch

[CC Switch](https://github.com/farion1231/cc-switch) 可管理供应商配置，从 [官方 Releases](https://github.com/farion1231/cc-switch/releases) 的 Assets 下载当前 Windows 安装包，运行安装程序后打开 CC Switch。不要把其他同名工具的配置方式混用。

## 六、CC Switch 与 WSL 的配置位置

先确认 Claude Code 运行在哪里：Windows 版 CC Switch 管理的 Windows 用户配置，不一定就是 WSL 中 `~/.claude/` 的配置。安装后先查看当前版本的 WSL 支持方式与实际写入位置，不假设 Windows 扩展、WSL CLI 和 Remote-WSL 扩展自动共用一份配置。

在 Claude Code 对应页面填写服务商提供的 Anthropic 兼容地址、API Key 和模型映射，模型名称以服务商当前文档为准。切换后退出旧会话，在 WSL 项目目录中重新执行 `claude`，检查实际响应。不要在多个配置文件和 shell 环境变量里同时保留互相冲突的供应商设置。

VSCode 扩展使用第三方供应商的配置方式见 [官方说明](https://code.claude.com/docs/en/vs-code)。涉及 `CLAUDE_CONFIG_DIR` 时填写扩展运行环境内的实际路径；Mac 的对应流程见 [Mac 配置](VSCode、ClaudeCode与CC%20Switch配置（Mac）.md)。

---

## 七、VSCode 中使用 Claude Code

### 1. 打开 Claude Code

- **终端模式**：WSL 终端中直接输入 `claude`，进入交互式对话
- **侧边栏模式**：VSCode 左侧点击 Claude Code 图标，或 `Ctrl+Shift+P` → **"Claude Code: Open"**

### 2. 基本用法

| 操作 | 说明 |
|---|---|
| 直接提问 | 在对话框中输入问题，Claude 会读取当前项目文件进行回答 |
| 代码编辑 | Claude 可修改文件；审批方式受当前权限模式影响，完成后查看 diff |
| 终端命令 | Claude 可执行命令，是否审批取决于当前权限设置 |
| `@file` 引用 | 使用 `@文件名` 让 Claude 聚焦特定文件 |
| 选中代码提问 | 在编辑器中选中代码段，`Ctrl+Shift+L` 发送到 Claude |

### 3. 常用 Slash 命令

| 命令 | 作用 |
|---|---|
| `/help` | 查看帮助 |
| `/fast` | 在支持的版本中切换快速模式；模型、费用以当前说明为准 |
| `/config` | 修改配置（主题、模型等） |
| `/clear` | 清空对话历史 |
| `/memory` | 管理持久化记忆 |

---

## 八、Skills 与 MCP

安装、配置位置和最小验证见 [技能与 MCP 工具](技能与MCP工具的安装及使用技巧.md)。WSL 内运行的 Claude Code，使用 WSL 用户的 `.claude/skills/` 和 MCP 启动环境。

以科研任务为例，可以先装当前需要的绘图、文献处理或输入检查技能。`find-skills`、`skill-creator` 等只有安装或由客户端提供后才可调用，不是所有环境都有的内置命令。技能涉及的 Python 包和外部程序仍需按说明安装。

## 九、使用小技巧

先在测试项目调用一个技能，检查实际生成的文件或工具返回，再用于正式工作。组合多个技能时明确每一步的输入、输出和单位；更新前保留已有配置，发现名称相同的技能时检查实际加载路径。

---

## 十、快速排错

| 问题 | 原因 | 解决方法 |
|---|---|---|
| `npm install` 卡住 | 网络、依赖或软件源问题 | 先读错误日志，再分别检查直连和代理 |
| `claude` 命令不存在 | npm 全局路径未加入 PATH | 在 WSL 执行 `command -v claude`，核对当前安装方式与 PATH |
| Claude Code 无法连接 API | 代理拦截或 API Key 无效 | `proxy_off` 关闭代理后重试；检查 `~/.claude/settings.json` 中的 `ANTHROPIC_AUTH_TOKEN` |
| VSCode 无法连接 WSL | WSL 未启动 | PowerShell 中执行 `wsl` 启动子系统 |
| ccswitch 切换后不生效 | VSCode 扩展未重启 | `Ctrl+Shift+P` → "Reload Window" |
