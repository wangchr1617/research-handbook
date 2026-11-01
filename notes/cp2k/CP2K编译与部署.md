# CP2K 编译与部署

**适用环境：Linux（集群原生编译与 Apptainer）；macOS（本机原生编译）；Windows（WSL，或为 Linux 准备文件）。**

已有可用的集群模块时，优先使用站点提供的 CP2K。自行编译前，先确定目标 CPU 架构、MPI、编译器及需要的功能，再按对应版本的[官方构建文档](https://manual.cp2k.org/trunk/getting-started/build-from-source.html)准备依赖。

## CP2K 2026.2 的源码流程

2026 系列采用 CMake；旧版 `ARCH=local` 的 Make 教程不能直接套用。优先从[官方发布页](https://github.com/cp2k/cp2k/releases)取得带版本号的发行压缩包，核对校验和，再进入解压目录。不要为重新编译而先删除整个 `arch/` 或软件安装目录。

Toolchain 可帮助安装编译器之外的依赖并生成构建配置：

```bash
cd tools/toolchain
./install_cp2k_toolchain.sh --help
./build_cp2k.sh --help
```

核对依赖选择后，常见流程为：

```bash
./install_cp2k_toolchain.sh
./build_cp2k.sh -j 4
```

`-j 4` 控制并行构建数，按实际分配的资源调整。辅助脚本需在 `tools/toolchain` 目录运行；安装前也应查看它打印的后续命令。不同版本的预设、参数和依赖组合可能变化，以所下载版本的帮助为准。

如果依赖已有系统版本，可按 toolchain 帮助选择 `system` 或给出目录；需要脚本安装的依赖选择 `install`。MPI 版需要匹配的 MPI 与 ScaLAPACK，其他可选库根据目标功能决定。离线环境应事先准备对应版本的完整源码与依赖，而不是临时跳过缺失库后假定功能完整。

手工管理依赖时，可直接用 CMake 配置独立的 `build/` 和安装目录，再执行 `cmake --build`、`cmake --install`。检查 CMake 配置摘要与 `CMakeCache.txt`，确认实际找到的编译器、数学库、MPI 和功能选项，不只看命令行中写了什么。

## 加载与运行检查

若使用辅助脚本生成的安装环境，先加载安装目录中的 `cp2k_env`；若由其他方式安装，则按该安装的路径加载环境。确认 `CP2K_DATA_DIR` 能找到基组和势文件，然后检查：

```bash
cp2k.psmp --version
```

`psmp` 为 MPI/OpenMP 版本，`ssmp` 为单进程 OpenMP 版本。启动 MPI 版时，使用与构建相匹配的 MPI 启动器，避免从另一套编译环境中混入库。

版本信息能说明程序及编译功能，实际可用性还需通过小计算检查。可先运行[水分子单点案例](../../examples/cp2k/minimal/single-point/)，核对 SCF、能量、受力和正常结束，再尝试[晶胞优化](CP2K晶胞优化.md)或其他目标任务。准备投入生产前，还应按版本文档运行适合该构建功能的回归测试。

## macOS、Windows 与集群的区别

Apple Silicon 使用 ARM64 编译器和依赖，Linux x86_64 集群使用相应架构的程序；两者的可执行文件不能直接互换。为特定 CPU 指令集优化的二进制，也不一定能在较旧计算节点运行。

Windows 用户可在 WSL 中按 Linux 方式准备环境，也可只在本机编辑文件、将计算交给 PBS 集群。编译器模块、网络下载及编译节点的使用方式按站点规定选择，不把某个课题组的节点名或模块版本当作通用命令。

## Apptainer 部署

容器适合固定依赖环境，但仍需选择与宿主 CPU 匹配的镜像。先核对 CP2K 镜像的版本、架构和入口，再按站点方式转换为 SIF；无需为运行已有镜像而手工修改容器内部的环境脚本。

MPI 容器还必须处理宿主与容器的 MPI 兼容性。[Apptainer 官方 MPI 指南](https://apptainer.org/docs/user/latest/mpi.html)介绍了混合与绑定两类方式。使用管理员提供的启动方式，先在计算节点验证单进程与多进程小案例，再扩展到多节点；容器能启动不等于集群 MPI 通信已验证。
