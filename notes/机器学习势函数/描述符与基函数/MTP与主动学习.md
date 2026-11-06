# MTP 与主动学习

**适用环境：通用（原理）；训练和动力学可使用 MLIP 实现。**

MTP（Moment Tensor Potentials，矩张量势）把邻域写成不同阶的矩张量，再把张量缩并成旋转不变量，用这些基函数拟合原子能。它是基函数展开路线，不要求使用深层神经网络。

## 一、历史与开发团队

Alexander V. Shapeev 在 2016 年正式发表 MTP，相关工作形成了 Skoltech 的 MLIP 方法与软件路线。Evgeny V. Podryabinkin 与 Shapeev 在 2017 年发表基于 D-optimality 的主动学习方法；2023 年的 MLIP-3 工作把主动学习进一步细化到原子环境。[^mtp][^al][^mlip]

## 二、矩张量是什么

记相对坐标为 $\mathbf r_{ij}$，定义

$$
M_{\mu,\nu}(i)=\sum_j
f_\mu(r_{ij},Z_i,Z_j)\,
\mathbf r_{ij}^{\otimes\nu}.
$$

$\mu$ 标识径向通道，$\nu$ 是张量阶数。$\nu=0$ 时是径向加权数值之和；$\nu=1$ 时是向量之和；$\nu=2$ 时，每个邻居贡献一个矩阵，其元素是 $r_\alpha r_\beta$。这些量保留邻域的几何信息。

向量会随旋转改变，但向量的点积不会。例如

$$
B(i)=M_{\mu,1}(i)\cdot M_{\mu',1}(i)
=\sum_{j,k} f_\mu(r_{ij})f_{\mu'}(r_{ik})
\mathbf r_{ij}\cdot\mathbf r_{ik}.
$$

右端包含 $\cos\theta_{jik}$，所以从两个一阶矩的缩并就能获得角度信息。更高阶矩与缩并产生更丰富的不变量。

原子能可写成 $\varepsilon_i=\sum_\alpha\xi_\alpha B_\alpha(i)$。若径向基已经固定，它对 $\xi_\alpha$ 线性；如果径向参数也一起优化，整体拟合便不再只是一次线性最小二乘。MTP 的 level 是控制基函数集合的约定，不等同于神经网络层数，也不应直接读作体阶。

## 三、主动学习如何挑构型

对线性系数而言，一个环境对应一行基函数读数。若已有行向量几乎覆盖同一方向，增加类似环境带来的信息有限。D-optimality 倾向选择能扩大设计矩阵所覆盖体积的样本，实践中用 maxvol 等方法及外推等级判断新构型是否离开已有覆盖。[^al]

外推等级不是“当前力误差多少 eV/Å”。它反映模型表示中的几何覆盖；参考方法本身错误、截断不足或遗漏电荷态时，即使等级不高也可能预测错误。

## 四、特点、参数与结果检查

MTP 适合作为可控展开阶数、较低推理成本和主动学习流程的候选。基函数数量随精度需求增长，多元素和复杂环境下仍要测量成本，不能只根据“线性”二字判断一定最快。

建议在固定数据集上扫描 cutoff、level 与正则化，同时记录能量、力、物性误差与实际 MD 速度。比较对象可选 [NEP](../局域神经网络/NEP与GPUMD.md)和 [ACE](ACE与多体展开.md)。主动学习的独立测试要求见[数据与主动学习](../基础与比较/数据与主动学习.md)。

## 实践：计算一个包含角度信息的矩不变量

以 1 Å 为长度单位，使数值距离无量纲，取 $f(r)=e^{-r}$；两个邻居与中心距离都为 1，夹角为 $\theta$。一阶矩 $M_1=e^{-1}(\mathbf r_1+\mathbf r_2)$，故

$$
M_1\cdot M_1=e^{-2}(|\mathbf r_1|^2+|\mathbf r_2|^2+2\mathbf r_1\cdot\mathbf r_2)
=2e^{-2}(1+\cos\theta).
$$

最后一步用了两个单位长度及点积定义。90° 时为 $2e^{-2}$，120° 时为 $e^{-2}$；零阶矩则始终为 $2e^{-1}$。因此即使径向分布相同，矩的缩并也能识别角度。完整数值代码见[描述符案例中的 `moment_features`](../../../examples/machine-learning/atomistic-models/descriptor_demo.py)。

```python
import numpy as np
r = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
weight = np.exp(-np.linalg.norm(r, axis=1))
m1 = (weight[:, None] * r).sum(axis=0)
print(m1 @ m1)
assert np.isclose(m1 @ m1, 2*np.exp(-2))
```

这是一项 MTP 型不变量的计算，不是完整 MLIP 模型：实际模型有多组径向基、元素通道、缩并及截断。

## 线性拟合与主动选择的实际矩阵逻辑

固定基函数后，对每个结构先累加所有原子的 $B_\alpha$，得到能量设计矩阵一行；对力标签则取基函数对坐标的负导数。拼接后的矩阵 $A$、标签 $y$ 和权重 $W$ 满足带正则最小二乘：

$$
\min_\xi\|W(A\xi-y)\|^2+\lambda\|\xi\|^2.
$$

实现时推荐 QR、SVD 或成熟最小二乘例程，避免直接求 $(A^TA)^{-1}$。能量、力和应力行的单位不同，权重会同时决定拟合侧重点与数值条件。若同时优化径向参数，则要在外层处理非线性，不再是一次 `lstsq`。

原生 MLIP 数据常用 `BEGIN_CFG` / `END_CFG` 结构块记录原子、超胞、能量和力。向软件提交前，先把一帧导回常用结构格式检查元素与坐标；外推等级高时，再按实际任务采样、去重和重新标注，不能把不稳定轨迹产生的任意重叠构型都交给 DFT。

## 参考资料

[^mtp]: A. V. Shapeev. Moment Tensor Potentials: A Class of Systematically Improvable Interatomic Potentials. *Multiscale Modeling & Simulation* **14**, 1153–1173 (2016). [论文](https://arxiv.org/abs/1512.06054)。
[^al]: E. V. Podryabinkin, A. V. Shapeev. Active learning of linearly parametrized interatomic potentials (2017). [论文](https://arxiv.org/abs/1611.09346)。
[^mlip]: E. Podryabinkin et al. MLIP-3: Active learning on atomic environments with Moment Tensor Potentials (2023). [论文](https://arxiv.org/abs/2304.13144)。

返回[分类导航](README.md)或[专题首页](../README.md)。
