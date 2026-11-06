# MatterSim

**适用环境：通用（原理）；实际运行按公开模型的依赖与硬件准备。**

MatterSim 的特点是把元素、温度和压力条件下的数据覆盖放在模型开发的中心。它说明通用势的发展不仅是换网络，还包括主动组织大规模参考数据。

## 一、历史与开发团队

Han Yang、Chenxi Hu、Yichi Zhou 等及 Microsoft Research AI for Science 团队于 2024 年公开 MatterSim。研究使用主动学习生成覆盖较广条件的第一性原理数据。公开 MatterSim-v1 模型采用 M3GNet 架构；不能把论文的全部实验模型、公开权重和后续服务版本视为完全相同的交付。[^paper][^code]

## 二、架构与数据路线

公开 v1 以含三体信息的图网络学习势能，通过能量导数获得力与应力。数据侧在多种结构和条件下探索，用参考计算补足薄弱区域，再训练模型。重要区别是：这里的温度和压力覆盖主要通过相应条件下的构型采样进入数据，不应直接理解成所有权重都把任意温压数值作为显式输入。

## 三、怎样理解论文中的条件范围

论文报告覆盖高温、高压的目标范围及一系列材料性质测试；这些范围描述开发与实验条件，不保证每种元素组合在整个范围内均有同样精度。用户的具体相、缺陷、熔体或反应仍应单独检查。

与主要采用弛豫轨迹的基础势相比，主动扩展非平衡与热力学条件的数据是重要区别。与专用 [DP](../局域神经网络/DP与DeePMD.md) 或 [NEP](../局域神经网络/NEP与GPUMD.md)相比，则需要比较零样本能力、微调成本和目标物性的实际精度。

## 四、结果检查

先在目标温压附近检查结构、力与应力，再比较体积响应、声子或自由能相关量。自由能不只是某个构型的势能，还涉及统计采样与熵。若研究相图，需要相间一致参考、采样误差和体系尺寸检查。

记录具体公开权重名、参考计算口径与软件版本，避免只写“使用 MatterSim”。模型及使用说明见[官方仓库](https://github.com/microsoft/mattersim)。

## 实践：金刚石 Si 的真实 calculator

```python
from ase.build import bulk
from ase.units import GPa
from mattersim.forcefield import MatterSimCalculator
atoms = bulk("Si", "diamond", a=5.43)
atoms.calc = MatterSimCalculator(device="cpu")
print("total eV:", atoms.get_potential_energy())
print("eV/atom:", atoms.get_potential_energy()/len(atoms))
print("forces:", atoms.get_forces())
print("stress GPa:", atoms.get_stress(voigt=False)/GPa)
```

这里沿用[官方最小例子](https://github.com/microsoft/mattersim#usage)的接口，首次运行需要取得权重。明确指定 CPU，避免把 Apple Silicon 上的设备兼容与数值表现混同于模型本身的误差。切换 5M 权重应按文档的 `load_path` 指定，不让默认选择在复现中隐式变化。

## 用同一案例检查热压数据覆盖的意义

从 Si 的 5.43 Å 开始，分别改变晶胞尺度并加入小幅随机位移；改变晶胞时使用 `set_cell(new_cell, scale_atoms=True)`，否则只改盒子却不等比例改位置，得到的不是所想的均匀应变。

体积扫描用于看能量、应力和结构响应是否一致；温度不能仅作为一个数“代入”上面 calculator 便得到自由能。热力学性质还需要势能面上的采样及统计分析。官方 v1 模型定位为体相材料，表面和长程作用相关任务应按模型卡另行核对或微调。

## 参考资料

[^paper]: H. Yang et al. MatterSim: A Deep Learning Atomistic Model Across Elements, Temperatures and Pressures (2024). [原始预印本](https://arxiv.org/abs/2405.04967)。
[^code]: Microsoft. [公开模型、架构和文档](https://github.com/microsoft/mattersim/blob/main/docs/index.rst)。

返回[分类导航](README.md)或[专题首页](../README.md)。
