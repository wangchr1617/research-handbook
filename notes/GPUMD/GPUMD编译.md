# GPUMD 编译指南

用 NEP 做分子动力学时运行 `gpumd`，用已有标注训练势时运行 `nep`。两者都由 GPUMD 源码构建。这里以 Linux 上的 NVIDIA CUDA 构建为例。若已有 LAMMPS 工作流，要把 NEP 接进去，可按[NEP-LAMMPS 编译](LAMMPS的NEP插件编译.md)准备 CPU 接口并验证同构型的能量与力。

## 一、先对齐 GPU、CUDA 与宿主编译器

从 [GPUMD 发布页](https://github.com/brucefan1983/GPUMD/releases)选择版本，解压后进入源码树的 `src/`。编译前先用 `nvcc --version` 和 `g++ --version` 检查实际调用的工具，并在目标 GPU 节点核对显卡型号与驱动。上游 Make 构建通过 `CUDA_ARCH` 指定目标算力（详见 [GPUMD 构建说明](https://github.com/brucefan1983/GPUMD#compile)），下面命令仅适用于工具链支持的 8.9 算力 GPU。更换 GPU 或工具链后，应先清理旧构建产物再重新编译。

```bash
make CUDA_ARCH="-arch=sm_89"
test -x gpumd && test -x nep
```

如果 `nvcc` 报不支持宿主编译器，先查 CUDA 版本支持的 GCC 范围。如果提示 GPU 架构不受支持，核对算力和 Toolkit 版本。例如上游说明 CUDA 13 已移除对 `sm_60` 的离线编译支持。旧节点上的 Intel MPI、GCC 路径应按本机模块配置选取，混用多个工具链的库路径会增加排查难度。

## 二、在 GPU 作业里跑通最小输入

编译产物可执行之后，在获分配 GPU 的计算环境中跑一份小输入。上游的 `examples/gpumd_dynamic/` 带 `run.in` 和 `model.xyz`，保持例子目录结构才能找到相对路径指向的势。若用自己的体系，按[两段短跑](GPUMD首个动力学与续算.md)检查热力学输出和重启文件。

PBS 脚本需按站点填写队列、GPU 资源和墙钟时间。下面是得到资源后执行的脚本主体。路径换成已验证的二进制，GPU 可见性沿用调度器分配。

```bash
set -eu
cd "${PBS_O_WORKDIR:?PBS_O_WORKDIR is unset}"
gpumd_bin=/path/to/GPUMD/src/gpumd
nvidia-smi -L
"$gpumd_bin" > gpumd.log 2>&1
```

若作业找不到 GPU，先核对请求的资源和计算节点上的设备可见性。若报缺少模型或输入，核对工作目录和 `run.in` 中的势路径。训练任务在备齐[训练输入](NEP训练.md)后改用同一构建产出的 `nep`。
