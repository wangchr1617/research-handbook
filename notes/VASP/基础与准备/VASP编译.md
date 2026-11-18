# VASP 编译与功能验证

**适用环境：Linux（集群编译与 PBS 运行）；macOS 使用匹配本机架构的工具链；Windows 建议使用 WSL/Linux。**

先看要跑的任务。普通多 k 点硅单点用 `vasp_std`，考虑 SOC 时需要 `vasp_ncl`，使用 VTST 或 VASPsol 则还要确认相应功能已经集成。已有管理员提供的构建时，可以直接按下面的算例验收。自行编译时，按源码版本选择模板，并保存工具链版本和 `makefile.include`。

## 一、按任务选择编译目标

从授权渠道取得源码，在源码目录选择 `arch/` 下最接近工具链的模板，再调整库路径：

```bash
cp arch/makefile.include.your_choice makefile.include
# 修改模板后，在允许编译的节点执行；4 为并行编译任务数。
make DEPS=1 -j4 all
make test
```

`all` 包含 `std`、`gam`、`ncl`；可只编译所需目标。三个可执行文件用途不同：标准计算、仅 Γ 点优化版本和非共线/自旋轨道计算。

Fortran、C/C++、MPI 包装器及 BLAS/LAPACK、ScaLAPACK、FFT 库应兼容。MKL 的链接参数取决于编译器与版本，不把旧版 `-mkl` 或 `-qmkl` 当成通用配置；线程数还需结合 [VASP 并行参数](VASP并行参数.md)设置。macOS 不能直接复用 Linux 的二进制库或模块名。

## 二、让批处理实际使用刚编译的程序

在[硅单点案例](../../../examples/vasp/minimal/single-point/README.md)的工作目录准备 Si 势。作业脚本会从 `VASP_EXEC` 取程序路径，可在脚本中显式设置为新构建的 `vasp_std`。提交后先核对 `OUTCAR` 的版本与电子收敛，再用同一套输入和 PAW 数据对照能量与受力。这样也会经过批处理实际使用的 MPI 启动方式。

遇到动态库错误，先核对模块、库路径和运行节点环境。遇到 GLIBC 版本不匹配，应换兼容构建或联系管理员，不通过全局替换系统运行库处理。

## 三、用对应算例验收扩展功能

补丁应与目标 VASP 版本对应，在独立源码副本中应用；保留未修改版本，记录补丁来源与修改。不要把针对 5.4、6.3 的逐行替换直接套到其他版本。

| 功能 | 配置与验证入口 |
| --- | --- |
| 标准能量与受力 | [单点计算](../结构与能量/VASP单点能与受力.md) |
| VTST 优化器与 CI-NEB | 按 [VTST 安装说明](https://theory.cm.utexas.edu/vtsttools/installation.html)集成，再运行 [NEB 案例](../../../examples/vasp/minimal/neb) |
| 固定部分晶格自由度 | 确认 `OPTCELL`/`IOPTCELL` 补丁的具体语义，见[固定晶格优化](../结构与能量/VASP固定晶格优化.md) |
| VASPsol 连续介质溶剂 | 按 [VASPsol 对应版本说明](https://github.com/henniggroup/VASPsol)配置，见[隐式溶剂计算](../结构与能量/VASP隐式溶剂计算.md) |

程序能启动不代表扩展功能已启用。固定晶格应检查整条晶格轨迹，VASPsol 应检查溶剂能项，NEB 应检查优化器、路径及受力。作业脚本的 `VASP_EXEC` 要指向对应程序。

参考：[VASP 6 安装说明](https://vasp.at/wiki/Installing_VASP.6.X.X)、[makefile.include 模板](https://vasp.at/wiki/Makefile.include)。
