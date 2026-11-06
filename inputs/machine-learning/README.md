# 机器学习模型输入

**适用环境：各模型对应的训练环境；JSON、YAML 和 INI 不可跨软件直接替换。**

这些输入配合专题笔记解释真实参数、数据布局和训练流程。除另有说明，保留上游示例的模型与数据设置；不附大型数据集、模型权重或计算软件。运行前按目标工作目录改写路径、硬件和训练预算。

## 输入与对应数据

| 本地文件 | 上游示例与用途 | 必须准备或调整 |
| --- | --- | --- |
| [deepmd-water.json](deepmd-water.json) | DeePMD `examples/water/se_e2_a/input.json` | 同仓库 `examples/water/data`，相对路径按原示例目录解析；默认百万步 |
| [nep-PbTe.in](nep-PbTe.in) | 参照 GPUMD PbTe 教程补充常用参数的小型 NEP4 起点 | 放入相容 `train.xyz`，改名 `nep.in`；需要 GPUMD 的 `nep` 可执行文件 |
| [nequip-tutorial.yaml](nequip-tutorial.yaml) | NequIP 当前 Hydra / Lightning 教程 | 按官方脚本准备 `fcu.xyz`，本机用 CPU、禁用 WandB、减小预算 |
| [allegro-tutorial.yaml](allegro-tutorial.yaml) | Allegro 当前 aspirin 教程 | 相容 NequIP / Allegro 环境，数据模块读取其教程数据；留意 `real` 单位 |
| [deeph-graphene.ini](deeph-graphene.ini) | 原始 DeepH-pack graphene | 准备 NPZ 矩阵数据，修改 raw/graph/save 路径；不是新软件 TOML |
| [deeph-e3-train.ini](deeph-e3-train.ini) | 原论文 DeepH-E3 的完整默认训练选项 | 填写图或预处理数据目录和输出目录；默认文件的空路径不能直接运行 |
| [hamgnn-v2.yaml](hamgnn-v2.yaml) | HamGNN `examples/V2.x/config.yaml` | 相容 `graph_data.npz`、轨道布局、H0、GPU/CPU 和 checkpoint |
| [deeptb-si-sk.json](deeptb-si-sk.json) | DeePTB silicon `tutorial_v2.2/input_2.json` | 硅能谱数据，基础 `nnsk` 拟合；输入默认 CUDA |
| [deeptb-si-environment.json](deeptb-si-environment.json) | 同教程 `input_3.json` | 基线 SK 初始化、环境编码及能谱数据；不能省略初始化步骤 |
| [deeptb-si-e3.json](deeptb-si-e3.json) | DeePTB `examples/e3/input_short_cpu.json` | Si64 的轨道矩阵和重叠数据；CPU，SLEM / `hamil_abs` |
| [deeptb-si-band.json](deeptb-si-band.json) | silicon 教程的能带后处理 | 实际训练 checkpoint、结构、参考能谱与相容费米能 |

## 用法与路径约定

模板文件名是便于查找的手册名称，不是各软件强制使用的默认名称。复制到独立计算目录后按笔记改为 `input.json`、`nep.in`、`train.ini` 或 `config.yaml`，同时复制或链接相应数据。相对数据路径由程序运行目录及其配置解析规则决定，不能仅因 JSON 合法就判断数据可用。

典型检查顺序：解析输入 → 确认元素/轨道与数据大小 → 小预算训练 → 验证误差 → 导出或推理 → 检查物理结果。语法解析通过不等于数据已经具备，也不等于模型已训练。

NequIP 与 Allegro 的本地副本移除了可选 `compile_mode: compile`，便于先用普通执行路径理解流程；其他模型设置保持上游示例；本地副本统一去除了行尾空白。正式加速按所用版本重新开启。`trainer.logger=false` 可避免教程默认的 WandB 配置要求；这不影响模型本身。

## 来源与版本快照

以下公开源码于 2026-11-06 核对。哈希表示核对时的上游仓库版本，手册笔记中的源码片段和这些输入以同一接口为背景；包安装时仍需匹配其依赖。

| 项目 | 对应源码快照 / 原始路径 | 保留的上游许可 |
| --- | --- | --- |
| DeePMD-kit | [`0edeaef` water 输入](https://github.com/deepmodeling/deepmd-kit/blob/0edeaef5617e9878edeb2346bf37bb6a035a4f51/examples/water/se_e2_a/input.json) | [LGPL](licenses/dplicense.txt) |
| NequIP | [`27d9d21` tutorial.yaml](https://github.com/mir-group/nequip/blob/27d9d2182da918ab7be0017d8300e53278f5e00e/configs/tutorial.yaml) | [MIT](licenses/nequiplicense.txt) |
| Allegro | [原始 tutorial.yaml](https://github.com/mir-group/allegro/blob/main/configs/tutorial.yaml) | [MIT](licenses/allegrolicense.txt) |
| GPUMD | [`9ed3a38` PbTe 案例](https://github.com/brucefan1983/GPUMD/tree/9ed3a38c29144b6e2fc790c63b5a46f7161972b5/examples/nep_train)；本地 NEP 文件为参数讲解用改写 | 具体软件与数据按上游许可 |
| DeepH-pack | [原始 graphene.ini](https://github.com/mzjb/DeepH-pack/blob/main/ini/graphene.ini) | [上游 LICENSE](licenses/deephlicense.txt) |
| DeepH-E3 | [`036bf95` train_default.ini](https://github.com/Xiaoxun-Gong/DeepH-E3/blob/036bf95b996052ef778c5c38e3c54c2ac0e2b591/deephe3/default_configs/train_default.ini) | [MIT](licenses/he3license.txt) |
| HamGNN | [`64dba1d` V2 配置](https://github.com/QuantumLab-ZY/HamGNN/blob/64dba1dbf445ccfa2683f560059c3fbca0df624a/examples/V2.x/config.yaml) | [GPL](licenses/hamlicense.txt) |
| DeePTB | [`597a036` silicon](https://github.com/deepmodeling/DeePTB/tree/597a0361d1111f4a6dce66996b366fd43442816c/examples/silicon/tutorial_v2.2)、[E3](https://github.com/deepmodeling/DeePTB/blob/597a0361d1111f4a6dce66996b366fd43442816c/examples/e3/input_short_cpu.json) | [LGPL](licenses/dtblicense.txt) |

上游输入和许可证按各自许可保留，不统一改写为本手册的 MIT。DeepH 的元数据与 LICENSE 标注应以所用发布的完整许可文件核对。

原理见[势函数](../../notes/机器学习势函数/README.md)、[哈密顿量](../../notes/机器学习哈密顿量/README.md)、[紧束缚模型](../../notes/机器学习紧束缚模型/README.md)；本地小型代码与数值例子见[配套案例](../../examples/machine-learning/atomistic-models/README.md)。
