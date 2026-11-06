# NEP 与 GPUMD

**适用环境：通用（原理）；GPUMD 训练与 MD 通常在 Linux GPU 环境执行。**

NEP（Neuroevolution Potential）使用可训练的局域描述符和紧凑前馈网络预测原子能。它的名字来自最初采用的自然演化策略优化方法，不是说原子结构通过遗传算法演化。

## 一、历史与开发团队

Zheyong Fan（樊哲勇）及合作者在 2021 年发表 NEP，原始合作包含渤海大学、Aalto University、香港大学、北京科技大学等团队。此后有 NEP2、NEP3 和 2024 年的 NEP4；GPUMD 官方文档按代际说明了模型变化。GPUMD 是训练与动力学软件生态，NEP 是其中的一类机器学习势。[^nep][^docs]

## 二、描述符怎样构造

径向分量写作

$$
q_n^i=\sum_jg_n(r_{ij}),\qquad
g_n(r)=\sum_k c_{nk}^{Z_iZ_j}f_k(r).
$$

$f_k$ 是含平滑截断的径向基，$c_{nk}^{Z_iZ_j}$ 是可训练系数。角向分量把径向函数与球谐函数组合，再形成旋转不变量；不同版本还包含更高体阶项。因此它兼有“按物理构造表示”和“从数据调整表示”的特点。[^docs]

把所有分量拼成 $\mathbf q_i$ 后，单隐藏层网络可写成

$$
\varepsilon_i=\sum_a w_a\tanh\!\left(\sum_bW_{ab}q_b^i-b_a\right)-b_0.
$$

邻居数可以变化，输入网络前先聚合成固定长度的描述符。由总能求导获得力，网络、径向函数和截断都要参与求导。

## 三、神经演化与架构是两件事

经典 NEP 训练采用 SNES（Separable Natural Evolution Strategy）：维护参数分布，采样一批参数，计算损失，根据优劣调整分布。它优化的是描述符和网络参数。推理阶段只计算最终模型，不再运行演化策略。

模型的函数形式与优化算法需要分开。后续实现可以为 NEP 型结构研究梯度训练，不应据名称断言所有扩展都只能采用 SNES；反过来，换优化器也不自动增加模型的长程物理。

## 四、参数、特点与边界

| 参数 | 改变什么 | 检查方法 |
| --- | --- | --- |
| 径向 / 角向 cutoff | 局域环境范围 | 对目标物性做收敛比较 |
| `n_max`、`basis_size` | 径向通道和展开分辨率 | 同时看验证误差与成本 |
| `l_max` | 角向和多体内容 | 按版本核对具体分量 |
| `neuron` | 网络宽度 | 避免仅按训练误差加宽 |
| 能量、力、virial 权重 | 训练目标平衡 | 检查单位与各项误差 |

NEP 的特点是紧凑表示、GPU 实现和面向大规模动力学、热输运的生态。高吞吐不意味着可以省去热流定义、尺寸效应和采样收敛检查。基础局域 NEP 的长程能力受截断限制；带动态电荷等扩展应作为独立模型核对。

## 五、如何开始实践

先运行一个已有元素映射的小数据训练，核对读入的原子数、能量和力，再检查有限差分与目标物性。训练代数只是预算，不能以“跑够十万代”代替收敛证据。独立测试集也不能按预测难度反复挑选。

具体步骤见 [NEP 训练](../../GPUMD/NEP训练.md)、[GPUMD 编译](../../GPUMD/GPUMD编译.md)和 [LAMMPS 接口](../../GPUMD/LAMMPS的NEP插件编译.md)。横向看 [MTP](../描述符与基函数/MTP与主动学习.md)、[DP](DP与DeePMD.md)和 [ACE](../描述符与基函数/ACE与多体展开.md)。

## 实践：PbTe 训练文件究竟包含什么

GPUMD 官方 `examples/nep_train` 使用 Te/Pb 数据，其最小 `nep.in` 只设置元素映射和训练代数。下面补充常用参数，完整文件见[PbTe 输入](../../../inputs/machine-learning/nep-PbTe.in)，保存为 `nep.in`，与配套 `train.xyz` 放在同一工作目录：

```text
type 2 Te Pb
version 4
cutoff 8 4
n_max 4 4
basis_size 8 8
l_max 4 2 0
neuron 30
lambda_e 1
lambda_f 1
lambda_v 0.1
population 50
generation 10000
```

这些参数用于该小例子，其他材料需重新测试。`type` 的顺序决定元素映射；两项 cutoff 分别控制径向与角向描述符，不能交换。`n_max=4` 对应索引 0 至 4，共五个通道，而不是四个。实际原始文件及数据入口见[GPUMD 官方 PbTe 案例](https://github.com/brucefan1983/GPUMD/tree/master/examples/nep_train)。

进入包含输入和数据的目录，运行训练程序 `nep`；其与动力学程序 `gpumd` 是不同可执行文件。输出中的 `nep.txt` 是模型，`loss.out` 是过程记录，`energy_train.out`、`force_train.out` 等用于预测–标签对比，不能只检查某一个文件生成。

## 按数组读预测结果

```python
import numpy as np
values = np.loadtxt("force_train.out")
print(values.shape)
assert values.ndim == 2 and values.shape[1] == 6
predicted, reference = values[:, :3], values[:, 3:]
rmse = np.sqrt(np.mean((predicted-reference)**2))
print("force component RMSE (eV/angstrom):", rmse)
```

这里使用该官方案例的六列力输出布局，前三列预测、后三列参考；其他版本先看格式说明。每一行是原子，而不是一帧构型，所以分母是全部力分量。若要按元素、温度或相态报告，需要保留每帧原子数和来源，才能把输出行映射回原始构型。

部署到新结构前再核对预测模式、单位、元素顺序和独立测试。使用官方 PbTe 数据并不能证明模型适用于 GeTe，尽管二者都有 Te。

## 参考资料

[^nep]: Z. Fan et al. Neuroevolution machine learning potentials: Combining high accuracy and low cost in atomistic simulations and application to heat transport. *Physical Review B* **104**, 104309 (2021). [原始论文](https://doi.org/10.1103/PhysRevB.104.104309)。
[^docs]: GPUMD. [NEP 模型、描述符与代际](https://gpumd.org/potentials/nep.html)、[训练输入](https://gpumd.org/nep/input_files/nep_in.html)。软件支持范围按所用版本核对。

返回[分类导航](README.md)或[专题首页](../README.md)。
