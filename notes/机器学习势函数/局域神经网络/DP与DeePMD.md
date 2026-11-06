# DP 与 DeePMD

**适用环境：通用（原理）；训练实践见 Linux 集群的 DeePMD 笔记。**

DP（Deep Potential）是学习势能面的模型路线，DeePMD-kit 是训练和部署相关模型的软件，DP-GEN 是组织探索、标注和训练的平台。这三个名称对应方法、实现和数据生产流程，阅读时应分别理解。

## 一、历史与开发团队

2018 年 Linfeng Zhang、Jiequn Han、Han Wang、Roberto Car 和 Weinan E 发表 DPMD，合作来自 Princeton、北京大学及中国工程物理研究院相关团队。同年的 DeepPot-SE（Smooth Edition）加入 Wissam A. Saidi 等合作者，改进对称表示与平滑性。后续 DeepModeling 社区扩展了软件后端、描述符和训练方法，不能把当前所有 DeePMD 模型都概括为最初的局域坐标版本。[^dp][^se]

## 二、经典 DeepPot-SE 架构

核心仍是 $E=\sum_i\varepsilon_i$，但环境表示由嵌入网络学习。以经典 `se_e2_a` 思路说明：

1. 收集截断内邻居，构造含平滑距离函数和单位方向的环境矩阵 $\widetilde R_i$，每行对应一个邻居。
2. 将径向信息送入嵌入网络，得到 $G_i$，其行仍对应邻居，列对应学习通道。
3. 通过矩阵乘积构造不变量，例如示意形式 $D_i=G_i^{\mathsf T}\widetilde R_i\widetilde R_i^{\mathsf T}G_i^{<}$；$G_i^{<}$ 表示保留的部分通道，归一化因实现而异。
4. 拟合网络把 $D_i$ 映射成原子能，对总能求坐标导数得到力。

中间的 $\widetilde R_i\widetilde R_i^{\mathsf T}$ 包含邻居方向的内积，所以几何角度可以进入不变量。矩阵乘法也把可变邻居数汇总为固定维度表示。这里是结构解释，完整输入与维度以对应描述符文档为准。[^docs]

## 三、演进与相邻方向

| 名称 | 解决的问题 | 阅读时关注 |
| --- | --- | --- |
| 早期 DP / DPMD | 对称局域表示与可扩展势能 | 局域坐标、邻居排序和平滑 |
| DeepPot-SE | 端到端的平滑对称表示 | 嵌入网络与环境矩阵 |
| 后续描述符与预训练模型 | 表示能力、多元素及迁移 | 具体架构、数据与权重版本 |
| DP-GEN | 数据覆盖和自动迭代 | 探索条件、分歧阈值、参考标注 |

DP-GEN 不会把短程模型变成长程模型，也不保证所有反应都已采样。需要显式电荷、极化或长程模块时，应单独核对模型设计。

## 四、适用特点与实践检查

DP 的优势是成熟的数据、训练、MD 接口和主动学习生态，适合围绕目标体系持续补数据。与 [NEP](NEP与GPUMD.md)相比，二者都可采用局域能量，但表示方式、优化器与实现不同；速度要用同硬件、同精度、同邻居规模实测。

重点检查元素顺序、能量基准、`sel` 或邻居容量、cutoff 平滑、应力转换以及导出模型接口。原子数增加并不要求重新训练固定大小网络，但新体系若出现训练外局部环境，仍可能失效。

操作见 [DeePMD 入门](../../DeePMD/DeePMD入门.md)、[安装](../../DeePMD/DeePMD安装.md)和 [DPGEN](../../DeePMD/DPGEN入门.md)。

## 实践：用官方水数据理解完整输入

配套[水的完整输入](../../../inputs/machine-learning/deepmd-water.json)使用 `type_map=["O","H"]`、`se_e2_a`、6 Å 截断和三层拟合网络。将它放到官方 `examples/water/se_e2_a` 工作目录，数据路径相对于当前工作目录解析，不能把输入复制到任意目录后仍假定 `../data` 有效。

```bash
dp --pt train input.json
dp --pt freeze -o model.pth
dp test -m model.pth -s ../data/data_3 -n 3
```

这是 PyTorch 后端的路径；TensorFlow 的 `.pb` 导出不应与 `.pth` 混用。训练预算、后端与官方快照见[输入来源说明](../../../inputs/machine-learning/README.md)。

以一帧含 $N$ 个原子的周期结构说明实际数据：`coord.npy` 每帧有 $3N$ 个坐标数，`box.npy` 有 9 个晶胞分量，`energy.npy` 是结构总能，`force.npy` 有 $3N$ 个力分量。`type.raw` 长度为 $N$，这里 0 代表 O、1 代表 H。把训练数据类型 0 误认成 H 不一定触发形状错误，却会改变全部化学含义。

## 对照网络参数与张量维度

`sel=[46,92]` 为不同元素的邻居容量，不能解释成水分子的 O/H 化学计量。`neuron=[25,50,100]` 属于描述符嵌入网络，`axis_neuron=16` 控制其中保留的轴通道；拟合网络另有 `[240,240,240]`。`rcut_smth=0.5` 是平滑区间的起点，不是“平滑宽度为 0.5 Å”。

以经典 SE 描述符的一种维度记法，环境矩阵为 `[N_neigh,4]`，嵌入为 `[N_neigh,M1]`，截取轴通道为 `[N_neigh,M2]`，组合后得到 `[M1,M2]` 不变量。这个维度说明了为什么 `axis_neuron` 必须与嵌入通道相容。

## 真实模型的 Python 推理接口

```python
import numpy as np
from deepmd.infer import DeepPot
potential = DeepPot("model.pth")
coords = np.load("../data/data_3/set.000/coord.npy")[:1]
cells = np.load("../data/data_3/set.000/box.npy")[:1]
types = np.loadtxt("../data/data_3/type.raw", dtype=int)
energy, forces, virial = potential.eval(coords, cells, types)
print(energy.shape, forces.shape, virial.shape)
```

核对 `potential.get_type_map()` 与数据类型表；`virial` 是能量单位的张量，转应力需按软件约定除以体积并处理符号。以上接口与导出流程分别见[官方推理](https://docs.deepmodeling.com/projects/deepmd/en/v3.0.0/_modules/deepmd/infer/deep_pot.html)和[冻结文档](https://docs.deepmodeling.com/projects/deepmd/en/latest/freeze/freeze.html)。

## 参考资料

[^dp]: L. Zhang et al. Deep Potential Molecular Dynamics. *Physical Review Letters* **120**, 143001 (2018). [原始论文](https://doi.org/10.1103/PhysRevLett.120.143001)。
[^se]: L. Zhang et al. End-to-end Symmetry Preserving Inter-atomic Potential Energy Model for Finite and Extended Systems (2018). [DeepPot-SE](https://arxiv.org/abs/1805.09003)。
[^docs]: DeepModeling. [DeePMD-kit 官方文档](https://docs.deepmodeling.com/projects/deepmd/en/stable/)。描述符与接口按安装版本核对。

返回[分类导航](README.md)或[专题首页](../README.md)。
