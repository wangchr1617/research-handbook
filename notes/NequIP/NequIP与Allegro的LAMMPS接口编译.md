# Allegro、NequIP 与 LAMMPS 编译

接到一个 Allegro 势文件时，先追到训练版本和导出方式，再决定如何编译 LAMMPS。这个顺序能避免一种常见返工：LAMMPS 能启动，也能识别 pair style，却在读模型时才发现新旧接口不相容。以下以 Linux x86_64 为例。

## 一、以模型来源选择接口

若模型出自仓库的[旧版 GeTe YAML](../../inputs/nequip/config.yaml)，可以从 `model_builders` 中的 `allegro.model.Allegro` 判断模型属于 Allegro。这个字段也表明该配置使用旧式训练入口。原环境记录为 NequIP 0.6.1、PyTorch 2.0.1、CUDA 11.7、Python 3.9 和 Open MPI 4.0.5。接手旧导出模型时先查当初的 Allegro 与接口提交。上游为旧模型保留了 Allegro 接口 v0.6.0，旧 NequIP 模型则查独立的 `pair_nequip` 仓库。能否复现上述旧环境还要取决于实际保留的安装包和提交。 [上游的新旧接口说明](https://github.com/mir-group/pair_nequip_allegro)

NequIP 0.7 后的工作流使用 `nequip-compile` 为目标接口生成模型。当前上游联合接口要求 2025 年 9 月 10 日版或更新的 LAMMPS，若启用 Kokkos，要使用默认的 double-double 精度模式。NequIP 消息传递模型的 `pair_style nequip` 仅支持一个 MPI rank，严格局域的 Allegro 可走 `pair_style allegro` 并用 MPI 扩展。若计划在多个 rank 上跑生产任务，应在选择模型架构时就考虑这个限制。 [联合接口的版本与执行要求](https://github.com/mir-group/pair_nequip_allegro)

## 二、让 CMake 使用与模型匹配的 PyTorch

下面是现代接口的 AOTInductor 构建示例。固定联合接口和 LAMMPS 的兼容版本，将两份源码放在同一父目录，激活用于模型编译的 Python 环境后，在父目录运行。此路线要求 PyTorch 2.6 或更新版本，以及与目标设备相容的工具链。若使用 Kokkos，额外核对 C++ ABI 和 GPU 架构。 [上游构建选项](https://github.com/mir-group/pair_nequip_allegro#installation)

```bash
(
    cd pair_nequip_allegro
    ./patch_lammps.sh ../lammps
)
torch_prefix=$(python -c 'import torch; print(torch.utils.cmake_prefix_path)')
cmake -S lammps/cmake -B lammps/build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$torch_prefix" \
    -DNEQUIP_AOT_COMPILE=ON
cmake --build lammps/build --parallel 4
lammps/build/lmp -help
```

读 CMake 输出确认 AOT 编译已启用，再从帮助输出检查目标 pair style。若 CMake 找不到 Torch，先查 Python 环境给出的路径。若二进制启动时报告 `GLIBCXX` 或未定义符号，核对编译器、LibTorch 的 C++ ABI 和运行时实际加载的 `libstdc++`。旧集群的记录曾遇到宿主库最高只提供 `GLIBCXX_3.4.19`，因此当时选择了 CUDA 11.7 对应的旧 ABI LibTorch。复现这类离线环境时，应同时确认 Python wheel、CUDA 依赖与 LAMMPS 链接库的来源，避免只换其中一个库。

## 三、让 GeTe 的同一构型在两端给出同样的力

在目标运行环境，用 `nequip-compile` 把同一份 checkpoint 或模型包编译成 LAMMPS 所需的产物。AOTInductor 下，Allegro 用 `--target pair_allegro`，NequIP 用 `--target pair_nequip`。下例使用 CPU，GPU 作业应在相容的目标设备上改用 `--device cuda`。 [模型编译文档](https://nequip.readthedocs.io/en/latest/integrations/lammps/pair_styles.html)

```bash
nequip-compile gete.nequip.zip gete-lammps.nequip.pt2 \
    --device cpu --mode aotinductor --target pair_allegro
```

把生成的模型路径填入 `pair_coeff`。如果模型类型名是 Ge、Te，而 LAMMPS 数据中的 1 号类型是 Ge、2 号是 Te，就在模型路径后按顺序填写 `Ge Te`。这个顺序可以在数据文件的类型定义与训练配置里核对。按[跨接口单点](NequIP模型部署与跨接口单点.md)验收能量与逐原子力。Allegro 若准备使用多 rank，继续用同一构型检查改变 rank 后的能量和力，再测吞吐。 [上游 pair style 用法](https://github.com/mir-group/pair_nequip_allegro#usage)
