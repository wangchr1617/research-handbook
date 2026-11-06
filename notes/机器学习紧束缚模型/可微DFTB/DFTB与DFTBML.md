# DFTB 与 DFTBML

**适用环境：通用（原理）；参数文件与元素覆盖按具体实现准备。**

DFTB（Density Functional Tight Binding）保留一个近似电子结构计算过程，机器学习则可调整其中的径向积分、在位参数或排斥项。它与直接学习势能面的神经网络势不同，也不等于所有经验 TB 的统称。

## 一、历史与开发团队

DFTB 来自对 DFT 能量及电荷响应的近似处理；Marcus Elstner、Thomas Frauenheim、Götthard Seifert 等合作于 1998 年发表 SCC-DFTB。后续 DFTB、DFTB+ 及扩展方法形成了多团队生态。[^scc]

Haichen Li、Christopher Collins、Matteus Tanha、Geoffrey J. Gordon 与 David J. Yaron 在 2018 年公开并发表把 DFTB 作为可训练层的工作。Frank Hu、Francis He 和 Yaron 于 2023 年发表 DFTBML，来自 Carnegie Mellon University 化学系，强调学习可解释的 DFTB 类模型参数。[^layer][^ml]

## 二、先理解能量由哪些部分组成

在常见二阶 SCC-DFTB 表示中，可示意写为

$$
E=\sum_n f_n c_n^\dagger H^0c_n
+\frac12\sum_{A,B}\gamma_{AB}\Delta q_A\Delta q_B
+E_{\rm rep}.
$$

第一项用参考密度产生的 $H^0$ 计算占据态贡献，第二项近似电荷涨落的能量，第三项补足排斥与其余近似贡献。$\Delta q_A$ 是相对于参考的电荷偏差，$\gamma_{AB}$ 描述相应相互作用；其符号约定需与电子数或电荷的定义一致。

此式不是把最终 SCC 哈密顿量的本征值简单求和后再原样加上正的二次电荷项。后者涉及重复计数修正，使用时应沿具体实现的总能表达。[^scc]

## 三、自洽过程为什么进入训练

参数决定 $H,S$，本征求解给出轨道与占据，轨道再决定电荷，电荷更新哈密顿量，如此迭代到收敛。若训练目标是能量或偶极，梯度要沿这条计算链回到参数。

```text
径向函数参数 → 组装 H、S → 自洽求解电荷与轨道
                                  ↓
更新参数 ← 损失反向传播 ← 能量、偶极等训练目标
```

这是算法逻辑，不是某个包的可执行 API。实现中要区分展开有限次迭代与对收敛解求导，并检查收敛精度、近简并和重叠病态对梯度的影响。

## 四、DFTBML 学习什么

DFTBML 通过灵活的一维径向函数等参数化学习相互作用，保留传统量子化学求解结构。其解释性来自模型结构与可检查的参数函数，不意味着每个拟合参数都可唯一对应一个可观测量。原论文还研究了数据量与模型形式带来的精度边界。[^ml]

与 [DeePTB-SK](../环境依赖SK/DeePTB-SK.md)相比，DFTBML 的核心是可微半经验电子模型的性质监督；与 [TBMaLT](TBMaLT.md)相比，后者是组织此类计算的工具框架，并非同一个已训练模型。

## 五、结果检查

先用未训练参数重现基线，核对能量分项、电荷守恒、$S$ 正定和 SCC 残差，再对参数做有限差分梯度检查。最后测试新分子或独立构型上的能量、偶极和曲线平滑性。若只修正排斥能，不能宣称电子能带也随之改善；要说明学习的具体分项。

## 实践：区分电子参数、排斥项与训练目标

学习一条径向函数时，可用三次样条保存离散参数。下面是可运行的插值与导数检查，而非伪造的 DFTBML API：

```python
import numpy as np
from scipy.interpolate import CubicSpline
r = np.array([1.0, 1.5, 2.0, 2.5])  # angstrom
v = np.array([-2.0, -1.0, -0.4, -0.1])  # eV, illustrative hopping values
spline = CubicSpline(r, v)
x, step = 1.8, 1e-5
fd = (spline(x+step)-spline(x-step))/(2*step)
assert np.isclose(fd, spline(x, 1), atol=1e-8)
```

这些数用于解释插值，不是某套可用于材料预测的参数。实际 DFTBML 需要在物理模型中组装这些积分，经过占据与自洽过程得到能量或偶极，再回传梯度。对样条的平滑性、单调约束、区间外行为和参考偏离正则，需要作为模型定义一起记录。

## 用 H2 解释为什么不能只拟合排斥总能

如果只调整 $E_{rep}(r)$，可以改变总能曲线与核力，但在电子参数不变时不会直接改变固定几何下的电子矩阵和本征值。因此“总能更准”和“能带更准”是不同目标。若同时调电子积分和排斥项，还可能有多个分项相互补偿。

对简单双原子扫描，分别保存 `E_band`、电荷响应项、`E_rep`、总能、键长和电荷。只有总能一列时，即使训练误差很小，也难以判断模型学到了哪一项。对完整分子电子矩阵与电子数的真实核对，可先运行[水分子自洽案例](../../../examples/machine-learning/atomistic-models/molecular_matrix.py)，再接 DFTB 专用参数和求解器。

原作者实现见[DFTBML](https://github.com/djyaron/DFTBML)。其模型与参数的训练范围需要按论文和发布数据说明，不能从一个 H2 或水例子推广到全部元素。

## 参考资料

[^scc]: M. Elstner et al. Self-consistent-charge density-functional tight-binding method for simulations of complex materials properties. *Physical Review B* **58**, 7260 (1998). [原始论文](https://doi.org/10.1103/PhysRevB.58.7260)。
[^layer]: A Density Functional Tight Binding Layer for Deep Learning of Chemical Hamiltonians. [原始论文与完整作者](https://arxiv.org/abs/1808.04526)、[期刊论文](https://doi.org/10.1021/acs.jctc.8b00873)。
[^ml]: F. Hu, F. He, D. J. Yaron. Treating Semiempirical Hamiltonians as Flexible Machine Learning Models Yields Accurate and Interpretable Results. *Journal of Chemical Theory and Computation* **19**, 6185–6196 (2023). [原始论文](https://doi.org/10.1021/acs.jctc.3c00491)、[代码与参数](https://github.com/djyaron/DFTBML)。

返回[分类导航](README.md)或[专题首页](../README.md)。
