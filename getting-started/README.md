# 从这里开始

按学习顺序阅读：[阅读目录](阅读目录.md)。

先准备工作环境，跑通一个小例子，再按课题查阅专题笔记。

## 第一次从哪里开始

没有准备过开发环境时，先读对应系统的“新生入门”。需要代理时从 [DOVE 的注册、购买与客户端下载](DOVE加速器配置与使用技巧.md#一注册购买和安装)开始；需要 AI 时先选 [Codex](Codex配置与使用技巧.md)或 [Claude Code](VSCode、ClaudeCode与CC%20Switch配置（Mac）.md)，安装客户端后再配置模型服务、技能和 MCP。

集群账号和校园 VPN 向课题组及学校申请；PBS、Module 通常由集群统一提供，不需要新生在个人电脑上先安装。Python、Docker 和编译工具按具体任务安装，不必一次全部装齐。

## 新生与本机环境

| 适用环境 | 文档 |
| --- | --- |
| Windows → Linux 集群 | [新生入门（Windows）](新生入门（Windows）.md) |
| macOS → Linux 集群 | [新生入门（Mac）](新生入门（Mac）.md)、[SSH 与密钥配置](Codex连接科研集群（macOS）.md) |
| Windows + WSL | [WSL 与 Docker 安装使用](WSL与Docker安装使用（Windows）.md)、[VSCode、Claude Code 与 CC Switch](VSCode、ClaudeCode与CC%20Switch配置（Windows）.md) |
| macOS | [VSCode、Claude Code 与 CC Switch](VSCode、ClaudeCode与CC%20Switch配置（Mac）.md)、[Docker 安装与使用](Docker安装与使用（Mac）.md) |
| Windows / macOS / Linux | [DOVE 加速器](DOVE加速器配置与使用技巧.md)、[浏览器代理配置](SwitchyOmega代理配置.md)、[Colab 入门](Colab入门.md) |
| iOS | [美区 Apple 账号注册](美区Apple账号注册（iOS）.md) |

## 集群与计算环境

| 主题 | 文档 |
| --- | --- |
| SSH 连接与密钥 | [macOS 本机 → Linux 集群](Codex连接科研集群（macOS）.md)、[Windows 新生入门](新生入门（Windows）.md) |
| Linux 基础 | [Linux 命令行使用与常用命令](linux/Linux命令行使用与常用命令.md)、[Linux 与集群工具导航](linux/README.md) |
| 提交和管理计算 | [PBS 作业管理系统使用](PBS作业管理系统使用.md) |
| 使用集群已有软件 | [Module 使用](Module使用.md) |
| Alkemie 服务部署 | [Mac → Linux](Alkemie集群部署（macOS）.md)、[Windows → Linux](Alkemie集群部署（Windows）.md) |
| Python 环境 | [Anaconda、Miniconda、Mamba](Anaconda、Miniconda、Mamba安装与使用.md) |
| Python 包与项目 | [pip 与 uv](pip与uv安装与使用.md) |
| 源码构建 | [高性能计算软件编译常识](高性能计算软件编译常识.md) |

## 记录与协作

[Git 与 Markdown 导航](git/README.md)按安装与首次提交、分支协作、文件管理与撤销、Markdown 排版组织。可先完成一次本地提交，再练习分支和 Pull Request。

## AI 工具

- [Codex 配置与使用技巧](Codex配置与使用技巧.md)
- [技能与 MCP 工具的安装及使用技巧](技能与MCP工具的安装及使用技巧.md)

## 应用开发

希望把 Python 工具或科研 Agent 做成可登录、可查询历史的应用，可以从[后端工程学习路线](../notes/后端工程/README.md)开始，配合[完整教学 Demo](../examples/backend/agent-demo/README.md)练习。已有 Docker 和 Linux 笔记可按需查阅。

希望构建论文问答或科研知识库，可从[知识工程专题](../notes/知识工程/README.md)学习文档解析、检索增强生成与图数据库。

## 学习路线

1. **准备环境**：按自己的系统阅读新生入门，确认本机、SSH 与文件传输可用。
2. **使用集群**：学习 Linux、Module 和 PBS，先提交一个小测试。
3. **记录与协作**：阅读 [Markdown 入门](git/Markdown入门.md)和 [Git 入门](git/Git入门.md)，尝试修改一篇笔记。
4. **动手计算**：运行 [RMSE 小案例](../examples/rmse/README.md)，核对结果和单位；再查阅[专题笔记](../notes/README.md)、[输入模板](../inputs/README.md)、[脚本](../scripts/README.md)和[案例](../examples/README.md)。
5. **记录学习与计算**：参考[记录模板](../templates/README.md)，记下输入、操作、计算条件和结果，方便以后查阅。

### 用一个材料问题串起理论与操作

准备使用 VASP 或 CP2K 时，先选课题相关的小模型，写清要比较的量，例如两种构型的能量差、某个原子的受力或一条振动模式。对照输入逐项解释结构与周期性、电子数和自旋、方法及数值精度，再运行对应的[最小案例](../examples/README.md)。遇到不理解的量，回到专题笔记、相应版本手册和基础教材补足概念，随后在例子中验证理解。

第二遍练习只改变一个有明确目的的设置，比较目标量和计算成本，并说明差异来自模型、方法还是数值精度。复现一张图后，还应能指出它读了哪个输出、采用什么单位和参考，以及哪些结果足以支持结论。把这组输入、检查与解释记录下来，再扩展到真实体系；不以输入能运行或图形相似作为掌握方法的判据。

## 从使用集群到搭建集群

掌握 SSH、Linux 与作业提交后，可进入[算力硬件与集群搭建专题](../notes/算力硬件与集群搭建专题/README.md)，练习需求测量、硬件选配、互联设计、Slurm 部署、验收和运维。
