# MACE

**适用环境：通用（原理）。**

MACE 将 ACE 的多体组合思路用于等变消息构造。阅读时把三个概念分开：MACE 是架构，`mace-torch` 是软件实现，MACE-MP 等是采用该架构训练出的权重系列。

## 一、历史与开发团队

Ilyes Batatia、Dávid Péter Kovács、Gregor N. C. Simm、Christoph Ortner 和 Gábor Csányi 在 NeurIPS 2022 发表 MACE，原始合作主要来自 Cambridge 和 University of British Columbia。后续 ACEsuit 社区及更广泛合作者推进实现、基础模型和应用。[^paper][^code]

## 二、为什么在消息里做多体组合

普通邻居消息从单条边读取信息，多层更新逐步组合环境。MACE 先把径向、球谐和邻居特征聚合为等变通道，再在同一中心上对这些通道做多次乘积和角动量耦合，让一条消息就包含更高阶的邻居相关性。

示意流程为

$$
A_i=\sum_j\phi(h_j,r_{ij},\widehat{\mathbf r}_{ij}),\qquad
B_i^{(\nu,L)}=\mathcal C_L[\underbrace{A_i\otimes\cdots\otimes A_i}_{\nu\text{ 次}}].
$$

$\mathcal C_L$ 表示按角动量耦合到输出阶 $L$。网络再混合这些通道并更新特征。详细含义见 [ACE](../描述符与基函数/ACE与多体展开.md)和[张量积入门](等变性与张量积入门.md)。这里是结构示意，并非逐项照写软件内部计算式。

## 三、相关阶与层数怎样理解

相关阶决定一次局部组合使用多少份邻域投影，角阶决定方向表示，层数决定信息传播。增加相关阶可以在较少层数中获得丰富的多体消息，但不代表所有 MACE 模型都必须使用固定两层或固定四体。

原论文预印本和会议摘要在实验设置与层数描述上存在版本差异。复现时以采用版本的正文、补充材料和配置为准，不把摘要中的某个数字写成架构定义。经过多层和非线性更新后，整个网络的有效体阶也不能只用初始相关阶概括。[^paper]

## 四、特点与限制

MACE 把显式多体表示与等变学习结合，可用于从小数据专用势到大数据预训练势。其成本受元素数、通道、角阶、相关阶和实现影响，不能仅比较参数数量。模型仍需要足够的数据覆盖，局域截断也不会因为使用高阶消息就自动消失。

若研究有机分子、无机固体或界面，应首先选择与标签口径和数据域相符的权重，再考虑微调。[MACE-MP 与 MACE-OFF](../通用基础势/MACE-MP与MACE-OFF.md)专门讨论这个区别。

## 五、结果检查

在固定数据划分上对比相关阶和层数，检查力的有限差分、旋转对称性、目标势垒或曲率。若导出到不同后端，使用同一构型对比能量、力与应力，避免只有能量一致而求导路径不同。

## 实践：从一份 extxyz 到 MACE 训练

在已安装 `mace-torch` 的环境中，准备按独立来源划分的 `train.extxyz` 与 `valid.extxyz`。每帧记录元素、Å 坐标、总能 eV 和力 eV/Å，明确能量字段名为 `energy`、力字段名为 `forces`。一个小网络的命令起点为：

```bash
mace_run_train --name=Si_demo --model=MACE \
  --train_file=train.extxyz --valid_file=valid.extxyz \
  --energy_key=energy --forces_key=forces \
  --E0s=average --r_max=5.0 --num_interactions=2 \
  --hidden_irreps='16x0e + 16x1o' --correlation=3 \
  --batch_size=2 --max_num_epochs=20 --device=cpu --default_dtype=float64
```

参数名来自[MACE 官方训练指南](https://mace-docs.readthedocs.io/en/latest/guide/training.html)。`E0s=average` 从训练能量拟合元素参考偏移，只提供初始化与基准，不能把不同泛函的数据物理差异都吸收掉。`num_interactions` 是交互层数，`correlation` 是局部乘积相关阶，`hidden_irreps` 是通道类型及重数。二十轮只用于流程学习，精度要看验证。

## 不依赖外部数据的完整训练案例

配套 [Cu/EMT 训练脚本](../../../examples/machine-learning/atomistic-models/train_mace_emt.sh)可直接生成数据并训练。它使用 `make_emt_dataset.py` 构造 24 个轻微畸变的 Cu 常规胞，按固定规则保留四个验证构型，用 `REF_energy` 和 `REF_forces` 明确标注字段，然后训练 100 轮小型 MACE，最后用 `MACECalculator` 从磁盘加载模型核对预测。

这里学习目标是 ASE 的 EMT 势，不是 DFT，目的是让读者实际看到数据 → 损失 → 检查点 → 独立进程推理。小数据上的拟合不能推出真实材料的第一性原理精度。完整脚本包含所有命令和输出位置，不依赖上面命令中的未提供训练文件。

## 真实预训练推理与结构扫描

配套[MACE 硅案例](../../../examples/machine-learning/atomistic-models/mace_silicon.py)调用已加载模型的 ASE calculator，对金刚石 Si 做晶格常数扫描、超胞能量可加性和力的有限差分检查。它加载固定的预训练 `small` 权重，区别于随机初始化的网络。包版本、权重文件 SHA256 和结果一起保存，便于区分“架构一样”与“同一个已训练模型”。

一个推理骨架为：

```python
import torch
from ase.build import bulk
with torch.serialization.safe_globals([slice]):
    from mace.calculators import mace_mp
atoms = bulk("Si", "diamond", a=5.43)
atoms.calc = mace_mp(model="small", device="cpu", default_dtype="float64")
print(atoms.get_potential_energy(), atoms.get_forces().shape)
```

第一次运行会取得权重。总能与每原子能差一个原子数因子；ASE 的 stress 使用 eV/Å³，不能直接与以 GPa 输出的其他模型比较。网络及检查点的具体实现见[官方代码](https://github.com/ACEsuit/mace)。

## 参考资料

[^paper]: I. Batatia et al. MACE: Higher Order Equivariant Message Passing Neural Networks for Fast and Accurate Force Fields. *NeurIPS* **35** (2022). [会议论文](https://papers.neurips.cc/paper_files/paper/2022/hash/4a36c3c51af11ed9f34615b81edb5bbc-Abstract-Conference.html)、[预印本及版本历史](https://arxiv.org/abs/2206.07697)。
[^code]: ACEsuit. [MACE 官方实现与贡献者](https://github.com/ACEsuit/mace)。

返回[分类导航](README.md)或[专题首页](../README.md)。
