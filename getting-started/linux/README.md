# Linux

按学习顺序阅读：[阅读目录](阅读目录.md)。

先学目录与文件操作，再理解环境、脚本和远程同步。下面的练习不要求普通用户维护共享系统。

| 笔记 | 内容与环境 |
| --- | --- |
| [Linux 命令行入门](Linux命令行使用与常用命令.md) | 登录、文件、查看输出、文本编辑 |
| [环境变量与文件权限](Linux环境变量与文件权限.md) | Linux；PATH、shell 配置、权限与空间 |
| [Bash 脚本与批量操作](Bash脚本与批量操作.md) | Linux / macOS / WSL / Git Bash；循环、参数与日志 |
| [SSH 连接与文件同步](SSH连接与文件同步.md) | 本机 → Linux；SCP、rsync 与结果下载 |
| [Module 使用](../Module使用.md) | Linux 集群；加载已有软件 |
| [Module 环境管理](Module环境管理.md) | Linux；编写个人 modulefile |
| [PBS 作业管理](../PBS作业管理系统使用.md) | Linux 集群；提交、查询与作业依赖 |
| [登录欢迎界面](登录欢迎界面配置.md) | Linux；个人或管理员定制提示 |
| [Linux 命令参考（CHM）](Linux命令参考.chm) | 补充参考，需要 CHM 阅读器 |

本机和集群的目录、配置与权限分别生效。耗资源的计算及大规模后处理在调度器分配的资源中运行。
