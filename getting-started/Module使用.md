# Module 使用

**适用环境：Linux 集群，已由管理员安装 Environment Modules 或 Lmod。**

集群中同一个软件可能有多个版本。Module 通过修改当前 shell 的环境变量，让你选用需要的编译器、MPI 和程序，不需要每次手动拼接路径。

## 开始前

先取得集群账号并按 [Mac](新生入门（Mac）.md)或 [Windows](新生入门（Windows）.md)教程登录 Linux。普通用户通常不需要下载和安装 Module，由管理员统一提供。

如果登录后 `type module` 报错，向管理员索取初始化方法；不要在 Mac 上安装一个同名软件，就认为能管理集群软件。需要自行维护 Linux 模块系统时，再查 [Environment Modules 官方安装文档](https://modules.readthedocs.io/en/latest/INSTALL.html)，个人软件的 modulefile 示例见本文第四节。

## 一、查看已有软件

```bash
type module
module avail
module list
```

`module` 常是 shell 函数，不一定能用 `which module` 找到。提示 `module: command not found` 时，先按管理员说明加载初始化脚本，不要自行改 `/etc/profile`。

如果管理员确认模块目录是 `/opt/modulefiles`，可执行：

```bash
module use /opt/modulefiles
module avail
```

`module use` 会增加搜索路径；直接 `export MODULEPATH=/opt/modulefiles` 则会覆盖原来的路径，可能把系统已有模块隐藏掉。

## 二、加载、检查和切换

下面用 `gcc/9.3` 举例，实际名称以 `module avail` 为准：

```bash
module show gcc/9.3
module load gcc/9.3
module list
command -v gcc
gcc --version
module unload gcc/9.3
```

`module show` 看它准备修改什么，`module list` 看已加载什么，程序的版本输出才说明最终调用了什么。如果路径仍指向别的版本，检查 Conda 环境、PATH 顺序或 shell 的命令缓存。

换整套工具链前记录当前模块，必要时在新终端测试。`module purge` 会卸载当前模块，可能连站点默认环境一起卸载；不要在正在准备其他任务的 shell 中随手执行。

Lmod 还常提供 `module spider 软件名` 搜索需要先加载编译器才能看到的模块；Environment Modules 的可用命令依版本而异，使用 `module help` 确认。

## 三、在 PBS 脚本中加载

登录终端和批处理作业是不同进程。不要只在登录时加载一次，就假设计算节点环境完全相同。

在 PBS 脚本运行程序之前，显式初始化 Module 并加载软件，例如：

```bash
# 初始化路径由管理员提供，下面只是常见示例
source /etc/profile.d/modules.sh
module load gcc/9.3
# 再加载与该编译器匹配的 MPI 和软件模块
module list
command -v gcc
```

先用小作业确认计算节点能找到同一套程序和动态库。编译时用一种 MPI，运行时换另一种 MPI，常会出现缺符号、启动失败或异常结果。

> **ps**：不建议在 `~/.bashrc` 里自动加载一长串计算软件。每个作业只加载自己需要的版本，比日后排查环境冲突省事。

## 四、自己编译的软件也可以写模块

在个人目录中组织 modulefile，例如 `~/modulefiles/mytool/1.0`：

```tcl
#%Module1.0
module-whatis "mytool 1.0"
conflict mytool
set root $env(HOME)/Software/mytool/1.0
prepend-path PATH $root/bin
prepend-path LD_LIBRARY_PATH $root/lib
```

`mytool` 和安装路径均为示例。没有动态库目录时不要添加对应行。加载后检查程序，再卸载确认路径恢复：

```bash
module use "$HOME/modulefiles"
module load mytool/1.0
module show mytool/1.0
module unload mytool/1.0
```

`prepend-path` 在搜索路径前添加目录，`setenv` 设置普通变量；编写和默认版本设置见 [Module 环境管理](../notes/linux/Module环境管理.md)。命令细节参考 [Environment Modules 手册](https://modules.readthedocs.io/en/latest/module.html)。
