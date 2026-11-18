# Orb

**适用环境：通用（原理与模型选择）。**

如果要用 Orb 跑 NVE，先从一帧轻微畸变的 Cu 开始。用相同的坐标和位移检查两种权重返回的力，再决定哪些分支值得进入轨迹测试。仓库的硅有限差分脚本提供了检查方法，可以替换为 Cu 和对应计算器。 [已有有限差分例子](../../../examples/machine-learning/atomistic-models/mace_silicon.py)

Orb 家族适合用来理解三个可独立选择的设计：是否严格旋转等变、力是否来自能量梯度，以及邻居图是否限制最大邻居数。不能只根据一个家族名判断这三个问题。

## 一、先认清各分支解决的问题

Orbital Materials 团队在 2024 年公开 Orb，2025 年发布 Orb-v3。v3 作者包括 Benjamin Rhodes、Sander Vandenhaute、Vaidotas Šimkus、James Gin、Jonathan Godwin、Tim Duignan 和 Mark Neumann。其重点是精度、时延、显存与体系规模之间的权衡。[^orb][^v3]

## 二、从权重设置看力与邻居图

Orb 采用高效的图网络路线，并探索通过旋转增强训练处理方向关系。Orb-v3 家族包含直接力和守恒力等不同分支；是否严格满足能量梯度关系取决于具体变体，而非“Orb”三个字。官方实现与模型卡是选权重的依据。[^code]

| 选择 | 意义 | 需要核对 |
| --- | --- | --- |
| 直接预测力 | 网络输出力向量 | 与能量梯度是否一致 |
| conservative 分支 | 用能量导数产生力 | 导数平滑性与数值精度 |
| 限制邻居数 | 降低图规模与成本 | 邻居切换是否引入不连续 |
| 不限邻居数 | 保留截断内完整邻域 | 高密度环境的成本 |

非严格等变并不等于所有预测都错误，旋转增强能改善实际误差；但它与架构保证的精确对称性不同。是否足够应通过目标任务测试。

## 三、为什么直接力模型需要单独检查

若 $\mathbf F=-\nabla E$，沿闭合路径的功理想情况下为零。独立预测的力没有自动满足此条件，能量、力与二阶响应之间可能不一致。结构搜索、长时间 NVE、声子与弹性对这些关系的要求不同。

因此比较速度时，要说明是否为能量求导模型、是否限制邻居数，以及测试结构的邻居密度。不同物理约束下的最快结果不能当作同一种任务的直接比较。

## 四、用同一构型检查力和对称性

对同一结构做多次旋转，检查能量和力误差；沿一个小闭合位移回路检查功，或直接与能量有限差分比较。再评估目标物性、长时间稳定性和实际 MD 时延。各变体的训练数据也要核对，不能省略权重后缀。

### 固定守恒力与不限邻居数的权重

下面的示例采用返回“模型 + 结构适配器”的接口，不与旧版只返回模型的代码混用：

```python
from ase.build import bulk
from orb_models.forcefield import pretrained
from orb_models.forcefield.inference.calculator import ORBCalculator
model, adapter = pretrained.orb_v3_conservative_inf_omat(device="cpu", precision="float64")
atoms = bulk("Cu", "fcc", a=3.58, cubic=True)
atoms.calc = ORBCalculator(model, atoms_adapter=adapter, device="cpu")
print(atoms.get_potential_energy(), atoms.get_forces())
```

`conservative` 标识能量导数力分支；`inf` 标识该变体不以固定最大邻居数截断图；`omat` 标识训练数据路线。`inf` 不代表相互作用延伸到无限距离，几何 cutoff 仍然存在。代码来源见[官方 ASE 接口](https://github.com/orbital-materials/orb-models#usage-with-ase-calculator)，安装版本若返回不同对象，应使用对应 tag 的文档。

### 从一个力分量走到闭合位移与轨迹

保持 Cu 晶胞不变，给一个原子小幅位移。分别向前和向后取能量差分，对照同一点、同一方向的输出力，并用几种位移步长检查差分稳定性。整体旋转测试要把晶胞和坐标一同旋转，核对旋转后的力。若做闭合回路测试，可逐段积分力与位移的点积，再减小沿路径的采样间隔检查积分误差。 [能量与力的判据](../基础与比较/势函数的学习对象与数学基础.md)

邻居容量的问题可用压缩扫描暴露：随着晶胞缩小，邻居数量增加；记录每个原子的实际度数及能量、力连续性，不能只看一个平衡晶胞的耗时。对 NVE 轨迹还应同时扫描时间步长，区分积分误差和模型不守恒。

### 参考资料

[^orb]: M. Neumann et al. Orb: A Fast, Scalable Neural Network Potential (2024). [原始论文](https://arxiv.org/abs/2410.22570)。
[^v3]: B. Rhodes et al. Orb-v3: atomistic simulation at scale (2025). [论文](https://arxiv.org/abs/2504.06231)。
[^code]: Orbital Materials. [官方实现及模型说明](https://github.com/orbital-materials/orb-models)。

返回[分类导航](README.md)或[专题首页](../README.md)。
