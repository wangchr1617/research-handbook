# ACE 与多体展开

**适用环境：通用（原理）。**

ACE（Atomic Cluster Expansion，原子团簇展开）是一套构造局域环境基函数的框架。它既能用于线性势，也能进入非线性模型或等变网络。MACE 借鉴了这条思路，但 ACE 与 MACE 并非同一个软件或同一套固定模型。

## 一、历史与开发团队

Ralf Drautz 在 2019 年发表用于原子间势的 ACE 工作，来自 Ruhr-Universität Bochum 的相关研究。后续数学分析、实现和网络化路线由 Drautz、Christoph Ortner、Gábor Csányi 等多个团队及社区推进。2020 年 Drautz 又将框架扩展到向量、张量、磁性和电荷转移相关属性。[^ace][^tensor]

## 二、先聚合邻居，再相乘

从一个原子出发，用径向函数和球谐函数读出邻域：

$$
A_{nlm}(i)=\sum_j R_n(r_{ij})Y_{lm}(\widehat{\mathbf r}_{ij}).
$$

$R_n$ 区分距离，$Y_{lm}$ 区分方向。接着把若干个 $A$ 相乘，再按角动量规则耦合成标量或其他阶数的张量。标量基函数用于能量，非标量可表示具有方向的物理量。

为什么先求和有用？以两个通道为例：

$$
A_aA_b=\left(\sum_j\phi_a(\mathbf r_{ij})\right)
\left(\sum_k\phi_b(\mathbf r_{ik})\right)
=\sum_{j,k}\phi_a(\mathbf r_{ij})\phi_b(\mathbf r_{ik}).
$$

左端只需先计算两次邻居和，右端却显式表现出两个邻居的相关性。这就是常说的 density trick：通过邻域密度投影的乘积表示多体信息。乘积包含 $j=k$ 的项，因此不能简单把每个乘积都解释成只含不同原子的纯多体项。

## 三、相关阶、体阶与角阶

若一个局域项涉及中心原子和 $\nu$ 个邻居，其最高体阶为 $\nu+1$；相关阶常用来描述邻域投影相乘的次数。角阶 $l$ 描述方向分辨能力，与邻居个数不是一回事。径向阶、角阶和相关阶共同控制表示的丰富程度。

线性 ACE 写作 $\varepsilon_i=\sum_\alpha c_\alpha B_\alpha(i)$。若把不变量送进非线性函数，或把等变特征传到下一层，最终函数的有效体阶不能只用一个线性截断阶数概括。阅读论文时应分清局部构造和整个网络。

## 四、与 MTP、SOAP 和 MACE 的关系

| 路线 | 常见表示 | 连接点 |
| --- | --- | --- |
| MTP | 笛卡尔矩张量及缩并 | 同样构造多项式型不变量 |
| SOAP | 密度展开的功率谱及核 | 属于相关密度表示思路 |
| ACE | 系统组合多体基函数 | 可选线性、非线性或张量输出 |
| MACE | 高阶等变消息 | 将多体耦合用于网络消息构造 |

这些联系解释架构脉络，并不意味着有限参数、截断和训练方案不同的实现必然等价。实践中要同时检查基函数数量、正则化、数值条件和目标物性。

## 五、学习检查

尝试展开上面的 $A_aA_b$，指出 $j=k$ 和 $j\ne k$ 两类项；再说明为什么“角阶更高”不能直接推出“涉及更多原子”。完成后可读[等变性与张量积](../等变图神经网络/等变性与张量积入门.md)和 [MACE](../等变图神经网络/MACE.md)。

## 实践：把九个外积分量拆成三个表示

设 $T=\mathbf u\mathbf v^T$，将其拆成

$$
T_0=\frac{\operatorname{tr}T}{3}I,\qquad
T_1=\frac{T-T^T}{2},\qquad
T_2=\frac{T+T^T}{2}-T_0.
$$

逐项相加可验证 $T_0+T_1+T_2=T$：两项转置部分相消，迹项也相消。$T_0$ 由一个数确定，$T_1$ 有三个独立分量，$T_2$ 对称且无迹，有五个独立分量。这正是 $1\otimes1=0\oplus1\oplus2$ 的笛卡尔版本。

```python
import numpy as np
u, v = np.array([1., 2., 0.]), np.array([3., -1., 1.])
t = np.outer(u, v)
t0 = np.trace(t) / 3 * np.eye(3)
t1 = (t - t.T) / 2
t2 = (t + t.T) / 2 - t0
assert np.allclose(t, t0 + t1 + t2)
assert np.allclose(t1.T, -t1)
assert np.allclose(t2.T, t2) and np.isclose(np.trace(t2), 0)
```

## 基函数数量如何影响实际训练

假设每个 $A_{nlm}$ 包含元素通道、径向通道与角通道，相关阶为二时需要选择两组索引并耦合；相关阶为三时要选择三组，还需限制中间角动量、宇称和对称重复。它不是把 `correlation` 加一而成本完全不变。

以 Si 的专用线性 ACE 为例，可先用少量径向通道和低相关阶拟合结构能，再加入力行；只有在验证误差确实受表达能力限制时增加基集合。检查基矩阵的奇异值、列尺度和正则化，能避免高阶基强相关导致不稳定系数。

若想直接操作球张量而不手写耦合系数，可运行[e3nn 张量积案例](../../../examples/machine-learning/atomistic-models/equivariance_demo.py)。它展示真实库中的耦合接口；完整 ACE 势还要包含邻域密度、径向基、对称化和模型拟合。

## 参考资料

[^ace]: R. Drautz. Atomic cluster expansion for accurate and transferable interatomic potentials. *Physical Review B* **99**, 014104 (2019). [原始论文](https://doi.org/10.1103/PhysRevB.99.014104)。
[^tensor]: R. Drautz. Atomic cluster expansion of scalar, vectorial, and tensorial properties including magnetism and charge transfer. *Physical Review B* **102**, 024104 (2020). [原始论文](https://doi.org/10.1103/PhysRevB.102.024104)。

返回[分类导航](README.md)或[专题首页](../README.md)。
