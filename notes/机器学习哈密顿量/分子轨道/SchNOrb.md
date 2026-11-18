# SchNOrb

**适用环境：通用（原理）；原始示例面向分子电子结构。**

SchNOrb（SchNet for Orbitals）把预测对象从少量标量性质推进到原子轨道基下的哈密顿量与重叠矩阵，再通过本征求解恢复分子轨道信息。

同一水分子用同一原子轨道基求解两次，一个占据轨道的系数可能整体反号。此时更有用的对照是占据子空间与密度。下面沿仓库的水分子矩阵说明怎样检查。

## 一、为什么预测矩阵再求轨道

Kristof T. Schütt、Michael Gastegger、Alexandre Tkatchenko、Klaus-Robert Müller 和 Reinhard J. Maurer 于 2019 年发表 SchNOrb，合作来自 TU Berlin、University of Luxembourg、University of Warwick 等机构。它扩展 SchNet 思路，是从结构预测分子电子矩阵的重要早期代表。[^paper]

## 二、架构和输出

网络先构建原子环境特征，再形成与原子对相关的方向特征，把它们映射到不同轨道之间的矩阵块。原始工作联合学习总能、$H$ 和 $S$；得到矩阵后解 $Hc=\varepsilon Sc$，而非直接为每个轨道的任意相位系数单独回归。

这样做避开了直接预测轨道系数时的部分相位、能级交叉与排序问题，但矩阵仍依赖基的顺序与相位。原始实现还通过旋转数据增强学习正确的旋转行为，这与后来把严格等变约束写进架构的路线有区别。[^paper]

### 比较轨道前先处理相位和简并

把某列 $c_n$ 乘以 $-1$，密度中的 $c_nc_n^T$ 不变，但系数逐元素 MAE 可以很大。在简并空间还允许多列一起酉混合。比较波函数时采用相位对齐、重叠或子空间投影，比直接比较数组更符合物理对象。

## 三、特点与后续演进

预测一个中心对象后，可以从轨道和密度推导多种性质，减少每种性质单独训练一个黑箱的需求。不过可得到哪些量仍取决于基、近似和算符信息，不能自动宣称得到任意精确多电子可观测量。

[PhiSNet](PhiSNet.md)进一步在架构中显式处理等变性，[QHNet](QHNet.md)则关注等变矩阵预测的效率。周期体系的平移块与大尺度装配见 [DeepH](../周期体系/DeepH.md)。这些是发展方向的比较，并不表示所有模型都直接继承同一份实现。

## 四、用水分子检查占据和电子数

先固定基组与计算方法，检查 $H,S$ 的厄米性和 $S$ 正定性，再比较轨道能、HOMO–LUMO 间隙与目标密度。旋转测试应同时变换基，不能直接比较旋转前后矩阵每个元素是否相同。

原论文中的分子集合与单体系训练设置不等于跨任意分子的通用模型。对新分子迁移时，应按分子身份划分数据并独立评估。

### 从七维基重建五个占据轨道

先执行[PySCF 水分子案例](../../../examples/machine-learning/atomistic-models/molecular_matrix.py)。从七维基中的 $H,S$ 解出轨道，再比较密度和电子数。这解释 SchNOrb 类模型为什么要输出矩阵，而不是只输出一个 HOMO–LUMO gap。

```python
import numpy as np
from scipy.linalg import eigh
sample = np.load("results/water_rhf.npz")
eps, c = eigh(sample["hamiltonian"], sample["overlap"])
c_occ = c[:, :5]
p = 2*c_occ @ c_occ.T
assert np.isclose(np.trace(p @ sample["overlap"]), 10)
```

在这个 RHF 例子上，可把 `c_occ` 的任意一列整体乘以 −1，再重算密度。系数逐元素误差会变，但密度和电子数保持原值。对等占据子空间内的正交混合也可以做同样检查。若预测轨道使用了另一套基，要先统一基和顺序，再做子空间对照。

若模型分别学习 $H,S$，损失中不应让 $S$ 变为任意对称但非正定矩阵。可在数据处理、参数化和评估层分别约束；简单把预测 $S$ 对称化并不足够。

## 五、把同样的检查接到训练输出

原作者仓库的 [`src/scripts/run_schnorb.py`](https://github.com/atomistic-machine-learning/SchNOrb/blob/master/src/scripts/run_schnorb.py)负责训练/评估入口，[`extract_data.py`](https://github.com/atomistic-machine-learning/SchNOrb/blob/master/src/scripts/extract_data.py)处理参考数据。其软件发布属于早期 SchNetPack 生态，不能把当前 SchNetPack 的同名类与历史接口直接组合。

阅读源码时按三步追踪：数据字段如何保存 $H,S$ 及基信息；原子对特征怎样展开成矩阵块；训练指标怎样从矩阵转换为轨道量。复现论文需使用原始基组和数据；本文七轨道水例子用于验证同类矩阵流程。

### 参考资料

[^paper]: K. T. Schütt et al. Unifying machine learning and quantum chemistry with a deep neural network for molecular wavefunctions. *Nature Communications* **10**, 5024 (2019). [原始论文、方法与代码入口](https://doi.org/10.1038/s41467-019-12875-2)。

返回[分类导航](README.md)或[专题首页](../README.md)。
