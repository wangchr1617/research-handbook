# Module 环境管理

**适用环境：Linux；普通集群用户使用已安装的 Modules / Lmod，个人部署另按官方安装说明。**

Module 通过改变当前 shell 的环境变量切换编译器、MPI 和软件版本。日常加载命令先看 [Module 入门](../../getting-started/Module使用.md)，本篇补充个人 modulefile 的写法。

## 一、先使用现有环境

```bash
type module
module avail
module list
```

集群找不到 `module` 时向管理员确认初始化路径，不在个人账号中修改 `/etc/profile`。如果要在自己的 Linux 工作站安装，使用发行版的 `environment-modules` 包或 [官方安装说明](https://modules.readthedocs.io/en/latest/INSTALL.html)，不需要照搬历史 TCL 下载地址和旧版本。

管理员确认 `/opt/modulefiles` 是模块目录时，可用 `module use /opt/modulefiles` 增加搜索路径。直接覆盖 `MODULEPATH` 可能隐藏原有模块。

## 二、给自己安装的软件写模块

假设程序已安装在 `~/Software/myapp/1.0`，可建立 `~/modulefiles/myapp/1.0`，内容如下：

```tcl
#%Module1.0
module-whatis "myapp 1.0"
conflict myapp
set root $env(HOME)/Software/myapp/1.0
prepend-path PATH $root/bin
prepend-path MANPATH $root/share/man
```

`set` 定义 modulefile 内部变量；`prepend-path` 将目录放到环境变量前面。如果安装目录没有手册，不必添加 MANPATH。有 Linux 动态库时按真实安装目录添加 `LD_LIBRARY_PATH`，不要盲目把另一套编译器库放到最前面。

```bash
module use "$HOME/modulefiles"
module show myapp/1.0
module load myapp/1.0
command -v myapp
module unload myapp/1.0
```

路径与程序名称是示例。加载后验证程序版本，再卸载检查环境恢复；文件存在不代表程序已经构建完成。

## 三、常用 modulefile 语句

```tcl
setenv MYAPP_HOME $root
prepend-path PATH $root/bin
append-path CPATH $root/include
```

`setenv` 设置普通变量，`prepend-path`、`append-path` 修改路径列表并支持卸载时撤回。`conflict myapp` 用于阻止同类模块同时加载；编译器与 MPI 组合还要按本集群模块设计处理。

Environment Modules 的默认版本文件可以在 `myapp` 目录中写 `.version`：

```tcl
#%Module1.0
set ModulesVersion "1.0"
```

Modules 与 Lmod 在配置、模块层级和默认版本机制上存在差别，先用 `module --version` 确认实现，不把所有 Tcl 示例都当作任意版本通用语法。

## 四、用于 PBS 作业

批处理脚本先初始化 Module，再加载明确版本；编译与运行使用相配套的编译器、MPI 和数学库。将 `module list` 与程序版本写入日志，方便复现。

不要把很多软件自动加载到个人 `.bashrc`。需要切换工具链时，记录已有模块，优先在新终端中测试；`module purge` 会影响当前 shell 的全部模块。

参考：[Environment Modules 命令手册](https://modules.readthedocs.io/en/latest/module.html)。
