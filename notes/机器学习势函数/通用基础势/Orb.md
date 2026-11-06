# Orb

**适用环境：通用（原理与模型选择）。**

Orb 家族适合用来理解三个可独立选择的设计：是否严格旋转等变、力是否来自能量梯度，以及邻居图是否限制最大邻居数。不能只根据一个家族名判断这三个问题。

## 一、历史与开发团队

Orbital Materials 团队在 2024 年公开 Orb，2025 年发布 Orb-v3。v3 作者包括 Benjamin Rhodes、Sander Vandenhaute、Vaidotas Šimkus、James Gin、Jonathan Godwin、Tim Duignan 和 Mark Neumann。其重点是精度、时延、显存与体系规模之间的权衡。[^orb][^v3]

## 二、架构路线与变体

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

## 四、结果检查

对同一结构做多次旋转，检查能量和力误差；沿一个小闭合位移回路检查功，或直接与能量有限差分比较。再评估目标物性、长时间稳定性和实际 MD 时延。各变体的训练数据也要核对，不能省略权重后缀。

## 实践：明确选择 conservative / unlimited-neighbor 变体

下面采用官方 `main` 分支目前返回“模型 + 结构适配器”的接口，不与旧版只返回模型的代码混用：

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

## 不依赖名字的直接检查

对轻微畸变 Cu 胞做能量有限差分检查，然后改变整体旋转，比较预测力是否按同一旋转变换。直接力变体即使在测试集 MAE 很好，也要分别报告它与能量梯度的不一致程度。

邻居容量的问题可用压缩扫描暴露：随着晶胞缩小，邻居数量增加；记录每个原子的实际度数及能量、力连续性，不能只看一个平衡晶胞的耗时。对 NVE 轨迹还应同时扫描时间步长，区分积分误差和模型不守恒。

## 参考资料

[^orb]: M. Neumann et al. Orb: A Fast, Scalable Neural Network Potential (2024). [原始论文](https://arxiv.org/abs/2410.22570)。
[^v3]: B. Rhodes et al. Orb-v3: atomistic simulation at scale (2025). [论文](https://arxiv.org/abs/2504.06231)。
[^code]: Orbital Materials. [官方实现及模型说明](https://github.com/orbital-materials/orb-models)。

返回[分类导航](README.md)或[专题首页](../README.md)。
