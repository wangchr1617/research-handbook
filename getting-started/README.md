# 从这里开始

先准备工作环境，跑通一个小例子，再按课题查阅专题笔记。

## 第一次从哪里开始

没有准备过开发环境时，先读对应系统的“新生入门”。需要代理时从 [DOVE 的注册、购买与客户端下载](DOVE加速器配置与使用技巧.md#一注册购买和安装)开始；需要 AI 时先选 [Codex](Codex配置与使用技巧.md)或 [Claude Code](VSCode、ClaudeCode与CC%20Switch配置（Mac）.md)，安装客户端后再配置模型服务、技能和 MCP。

集群账号和校园 VPN 向课题组及学校申请；PBS、Module 通常由集群统一提供，不需要新生在个人电脑上先安装。Python、Docker 和编译工具按具体任务安装，不必一次全部装齐。

## 新生与本机环境

| 适用环境 | 文档 |
| --- | --- |
| Windows → Linux 集群 | [新生入门（Windows）](新生入门（Windows）.md) |
| macOS → Linux 集群 | [新生入门（Mac）](新生入门（Mac）.md)、[SSH 与密钥配置](../notes/getting-started/Codex连接科研集群（macOS）.md) |
| Windows + WSL | [WSL 与 Docker 安装使用](WSL与Docker安装使用（Windows）.md)、[VSCode、Claude Code 与 CC Switch](VSCode、ClaudeCode与CC%20Switch配置（Windows）.md) |
| macOS | [VSCode、Claude Code 与 CC Switch](VSCode、ClaudeCode与CC%20Switch配置（Mac）.md)、[Docker 安装与使用](Docker安装与使用（Mac）.md) |
| Windows / macOS / Linux | [DOVE 加速器](DOVE加速器配置与使用技巧.md)、[浏览器代理配置](SwitchyOmega代理配置.md)、[Colab 入门](Colab入门.md) |
| iOS | [美区 Apple 账号注册](美区Apple账号注册（iOS）.md) |

## 集群与计算环境

| 主题 | 文档 |
| --- | --- |
| Linux 基础 | [Linux 命令行使用与常用命令](Linux命令行使用与常用命令.md) |
| 提交和管理计算 | [PBS 作业管理系统使用](PBS作业管理系统使用.md) |
| 使用集群已有软件 | [Module 使用](Module使用.md) |
| Alkemie 服务部署 | [Mac → Linux](Alkemie集群部署（macOS）.md)、[Windows → Linux](Alkemie集群部署（Windows）.md) |
| Python 环境 | [Anaconda、Miniconda、Mamba](Anaconda、Miniconda、Mamba安装与使用.md) |
| Python 包与项目 | [pip 与 uv](pip与uv安装与使用.md) |
| 源码构建 | [高性能计算软件编译常识](高性能计算软件编译常识.md) |

## AI 工具

- [Codex 配置与使用技巧](Codex配置与使用技巧.md)
- [技能与 MCP 工具的安装及使用技巧](技能与MCP工具的安装及使用技巧.md)

## 学习路线

1. **准备环境**：按自己的系统阅读新生入门，确认本机、SSH 与文件传输可用。
2. **使用集群**：学习 Linux、Module 和 PBS，先提交一个小测试。
3. **记录与协作**：阅读 [Markdown 入门](../notes/git/Markdown入门.md)和 [Git 入门](../notes/git/Git入门.md)，尝试修改一篇笔记。
4. **动手计算**：运行 [RMSE 小案例](../examples/rmse/README.md)，核对结果和单位；再查阅[专题笔记](../notes/README.md)、[输入模板](../inputs/README.md)、[脚本](../scripts/README.md)和[案例](../examples/README.md)。
5. **记录学习与计算**：参考[记录模板](../templates/README.md)，记下输入、操作、计算条件和结果，方便以后查阅。
