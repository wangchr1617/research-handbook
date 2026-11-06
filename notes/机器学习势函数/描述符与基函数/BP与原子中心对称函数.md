# BP 与原子中心对称函数

**适用环境：通用（原理）。**

BP 势是理解现代机器学习势函数的一条起点：把原子附近的环境变成固定长度的特征，用小型神经网络预测原子能，再求和得到总能。先读[能量与力的基础](../基础与比较/势函数的学习对象与数学基础.md)，再看这里的环境编码。

## 一、历史与开发团队

Jörg Behler 与 Michele Parrinello 在 2007 年提出高维神经网络势框架，原论文作者单位为 ETH Zurich 在 Lugano 的研究团队。2011 年 Behler 系统整理了原子中心对称函数（ACSF）。这里介绍经典局域框架；后来的电荷平衡和长程扩展并不自动包含在原始 BP 模型中。[^bp][^acsf]

## 二、架构怎样处理不同邻居数

以径向 ACSF 为例：

$$
G_i^{\rm rad}=\sum_{j\ne i}
\exp[-\eta(r_{ij}-R_s)^2]f_c(r_{ij}).
$$

$R_s$ 是探测距离，$\eta$ 控制宽度，$f_c$ 在截断处平滑归零。这个量相当于问：“中心原子附近，离 $R_s$ 这么远的邻居有多少？”换几组 $\eta,R_s$，就得到一组不同距离尺度的读数。

只有距离无法区分同样键长、不同夹角的构型，所以再加入含 $\cos\theta_{ijk}$ 的角向函数。每个函数输出一个数，邻居再多也只改变这些读数，特征长度保持固定。距离与夹角不随整体旋转变化，求和不随邻居编号变化。

然后按中心元素选网络：$\varepsilon_i=\mathrm{NN}_{Z_i}(\mathbf G_i)$，并计算 $E=\sum_i\varepsilon_i$。多元素时还要按邻居元素区分描述符通道，否则不同化学环境可能得到相同编码。

## 三、与后续方法相比

| 方法 | 环境表示怎样获得 | 主要变化 |
| --- | --- | --- |
| BP / ACSF | 人工选择径向与角向函数 | 物理含义直观，需设计特征 |
| DP | 嵌入网络学习对称表示 | 减少手工描述符选择 |
| NEP | 可训练径向展开与多体不变量 | 联合优化紧凑描述符和网络 |
| 等变网络 | 保留可旋转的向量与张量 | 在中间层传递方向信息 |

BP 的价值是把“可扩展到不同原子数”和“满足基本对称性”做进结构设计。其限制是有限截断、有限描述符分辨率和多元素通道增长；网络再大也无法恢复输入已丢失的信息。

## 四、如何判断理解正确

画出两个中心键长相同、夹角不同的三原子构型。径向读数可以一样，角向读数应能区分它们。再整体旋转构型，所有标量描述符应保持不变。用不同网络输出的原子能比较“原子真实能量”没有直接物理依据，优先比较总能、力与目标物性。

继续阅读 [GAP 与 SOAP](GAP与SOAP.md)和 [DP](../局域神经网络/DP与DeePMD.md)。

## 实践：用真实 ACSF 实现区分键长与键角

以 O 为中心、两个 H 距离都为 1 Å 的三原子环境为例，只把 H–O–H 角从 90° 改为 120°。只统计 O–H 距离的径向函数不能区分二者；角向函数应当改变。下面调用 DScribe 的 ACSF 实现，而非手写一个形似 ACSF 的占位函数：

```python
from ase import Atoms
from dscribe.descriptors import ACSF

atoms = Atoms("OHH", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
acsf = ACSF(species=["H", "O"], r_cut=4.0,
            g2_params=[[1.0, 0.0]], g4_params=[[1.0, 1.0, 1.0]])
features = acsf.create(atoms, centers=[0])
print(features.shape)
```

`centers=[0]` 只计算 O 中心，因此第一维是 `1`；第二维是按元素组合和对称函数展开后的特征数，并不是原子数。`g2_params` 每行是径向的 $\eta,R_s$，`g4_params` 每行是角向的 $\eta,\zeta,\lambda$。`r_cut`、坐标和 $R_s$ 使用相同长度单位；$\eta$ 相应带倒长度平方。`species` 要覆盖整个数据集的元素，不能每帧随出现的元素任意改变列定义。

完整的[描述符案例](../../../examples/machine-learning/atomistic-models/descriptor_demo.py)实际生成两个角度、旋转和交换同种邻居，分别输出特征差。其矩张量、ACSF 和 SOAP 结果也可直接横向比较。这个例子解释输入表示；网络训练还要把所有中心的特征送入按元素共享的网络，再对总能求导。

## 训练代码中容易漏掉的求导链

设 $G_b$ 为第 $b$ 个描述符、$w$ 为网络参数，则

$$
F_{i\alpha}=-\sum_{j,b}\frac{\partial\varepsilon_j}{\partial G_{jb}}
\frac{\partial G_{jb}}{\partial R_{i\alpha}}.
$$

先对每个原子能求特征梯度，再乘描述符对坐标的导数，最后对所有受该坐标影响的中心求和。只求中心 $i$ 自己的能量导数，会漏掉它作为其他中心邻居时的贡献。若描述符先用 NumPy 或外部库算出，再转为 PyTorch 张量，PyTorch 不会自动知道前半段坐标导数；需要显式接入描述符导数或使用可微实现。

资料：[DScribe ACSF 接口](https://singroup.github.io/dscribe/latest/tutorials/descriptors/acsf.html)。

## 参考资料

[^bp]: J. Behler, M. Parrinello. *Physical Review Letters* **98**, 146401 (2007). [原始论文](https://doi.org/10.1103/PhysRevLett.98.146401)。
[^acsf]: J. Behler. Atom-centered symmetry functions for constructing high-dimensional neural network potentials. *Journal of Chemical Physics* **134**, 074106 (2011). [原始论文](https://doi.org/10.1063/1.3553717)。

返回[分类导航](README.md)或[专题首页](../README.md)。
