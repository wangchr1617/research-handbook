# VASPKIT 安装与基本使用

**适用环境：Linux、macOS；Windows（选择 Windows 二进制，或在 WSL 中使用 Linux 版）。**

从[官方发布页](https://sourceforge.net/projects/vaspkit/files/Binaries/)下载与操作系统、CPU 架构匹配的包，按包内说明解压和设置环境。[官方安装文档](https://vaspkit.com/installation.html)介绍了目录与配置文件。

## 安装与路径

Linux 集群优先使用管理员提供的模块；自行安装时，可将解压目录放在自己的软件目录。例如在 Bash 或 Zsh 配置文件中添加：

```bash
export VASPKIT_HOME="$HOME/Software/vaspkit"
export PATH="$VASPKIT_HOME/bin:$PATH"
```

将 `VASPKIT_HOME` 改为实际解压目录，再加载相应的 `~/.bashrc` 或 `~/.zshrc`。运行 `vaspkit`，确认能显示版本和主菜单。

macOS 应使用 macOS 包；Apple Silicon 若使用 Intel 二进制，还需满足 Rosetta 运行条件。Windows 原生与 WSL 的可执行文件、路径及配置分别管理，不要把 Windows 盘符直接填入 Linux 配置。

## 配置与功能检查

参照安装包中的 `how_to_set_environment_variable` 创建 `~/.vaspkit`，已有配置时合并所需设置。重点核对授权赝势目录 `PBE_PATH`、Python 路径 `PYTHON_BIN`，以及所需绘图配置；字段名以下载版本的模板为准。赝势文件不放入本仓库。

用一个简单 POSCAR 检查原子数、元素和晶胞是否正确读取，再尝试生成输入。生成 POTCAR 后仍需核对元素顺序和所用势；生成 INCAR 后核对任务参数，模板不是适合所有材料的默认答案。

如果原子数被读成零，或后续密度、声速出现 `NaN/Infinity`，应先检查输入格式、版本和运行架构，不要直接采用派生结果。

## 常用操作

操作菜单及编号见[官方教程](https://vaspkit.com/tutorials.html)。仓库中已配套的流程包括[态密度](../电子结构与成键/VASP态密度计算.md)、[能带](../电子结构与成键/VASP能带计算.md)、[弹性常数](../响应与输运/VASP弹性常数计算.md)、[光学性质](../响应与输运/VASP光学性质计算.md)与[能量—体积拟合](../结构与能量/VASP能量体积曲线拟合.md)。

交互流程稳定后，可将逐行输入存为文本文件：

```bash
vaspkit < vaspkit.in
```

查看对应案例里的 `vaspkit.in`，比将很长的转义字符串写进命令更容易核对。批量脚本还应检查工具日志和预期输出，而不是只检查退出码。中文扩展阅读：[VASPKIT 使用手册](https://github.com/tamaswells/VASPKIT_manual/blob/master/manual/VASPKIT%E2%80%94VASP%E8%BD%AF%E4%BB%B6%E9%A2%84-%E5%90%8E%E5%A4%84%E7%90%86%E5%B7%A5%E5%85%B7%E4%BB%8B%E7%BB%8D.md)。
