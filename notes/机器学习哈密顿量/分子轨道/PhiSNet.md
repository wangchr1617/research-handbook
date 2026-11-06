# PhiSNet

**适用环境：通用（原理）；以分子波函数和电子密度代理为背景。**

PhiSNet 关注如何在网络结构中保证分子旋转时输出按正确规则变化。它通过轨道矩阵等结构化对象恢复波函数与密度信息，属于电子结构学习路线，不是只输出总能的原子势。

## 一、历史与开发团队

Oliver T. Unke、Mihail Bogojeski、Michael Gastegger、Mario Geiger、Tess Smidt 和 Klaus-Robert Müller 于 NeurIPS 2021 发表相关工作，来自 Müller 团队及几何学习合作网络。原论文标题为“SE(3)-equivariant prediction of molecular wavefunctions and electronic densities”。[^paper]

## 二、架构怎样使用等变性

原子特征包含不同角阶的通道，与键方向的球谐特征按角动量规则耦合，再形成适合轨道对的输出块。相比主要依靠旋转增强约束输出的方案，架构内的等变运算能直接规定变换关系。

最终仍需在选定基中处理矩阵、本征求解和占据。波函数代理与多电子神经网络波函数不是同一个概念：这里的原子轨道表示及参考计算近似需要保留，不能把“预测波函数”理解为对任意关联态的精确求解。[^paper]

## 三、与 SchNOrb 和 QHNet 比较

| 方法 | 阅读重点 |
| --- | --- |
| [SchNOrb](SchNOrb.md) | 从结构到 $H,S$，早期分子矩阵学习 |
| PhiSNet | 显式 SE(3) 等变构件与波函数/密度表示 |
| [QHNet](QHNet.md) | 在等变约束下减少张量运算和内存成本 |

严格几何约束降低了网络需要从数据学习的自由度，但不替代化学空间覆盖。不同基组、电子数和参考方法会改变预测任务。

## 四、结果检查与使用边界

先检查旋转等变、矩阵结构和轨道能，再比较密度与所需派生量。若将预测用作传统自洽计算的初猜，最终仍应按原来的电子收敛标准验收；不能因为初猜接近就跳过收敛检查。

如果要从矩阵代理得到能量和力，需采用完整的总能表达与导数，而不是把本征值之和直接等同于总能。相关基础见[从轨道到哈密顿量矩阵](../基础与比较/从轨道到哈密顿量矩阵.md)。

## 实践：从等变电子表示走到轨道密度

PhiSNet 的中间原子特征可按 $l=0,1,\ldots,L$ 组织成多个角通道。如果每阶都有 $F$ 份，分量总数是

$$
F\sum_{l=0}^{L}(2l+1)=F(L+1)^2.
$$

例如 $F=16,L=2$ 时共有 $16(1+3+5)=144$ 个分量，而不是 $16\times2$。这说明提升最高角阶会同时增大表示与耦合路径数量。可先运行[e3nn 案例](../../../examples/machine-learning/atomistic-models/equivariance_demo.py)，直接检查同类不可约表示的维数与旋转。

下游密度流程可用[真实水分子矩阵](../../../examples/machine-learning/atomistic-models/molecular_matrix.py)复现：固定 $S$，由预测或参考 $H$ 求占据轨道，再构造 $P$。对于同一已知基，密度函数为 $\rho(\mathbf r)=\sum_{\mu\nu}P_{\mu\nu}\phi_\mu(\mathbf r)\phi_\nu^*(\mathbf r)$，因此“密度正确”还依赖基函数取值和占据，不能从矩阵均方误差直接推出。

## 公开实现与再实现的界限

除了原论文，可阅读 [nablaDFT 的 PhiSNet 实现](https://github.com/AIRI-Institute/nablaDFT)，其论文明确说明为适配分子批处理做了修改。这是研究再实现，不能称为原作者原封不动的发布。批处理时各分子可以拼成同一个大图，但不同分子之间不能产生边；读出矩阵也必须按分子分别装配。

若用预测密度作为 PySCF 的 SCF 初猜，可调用 `mf.kernel(dm0=predicted_density)`，然后按同一收敛阈值继续迭代。检查初猜前后迭代数、最终能量和密度差；少迭代并不允许降低最终收敛要求。

## 参考资料

[^paper]: O. T. Unke et al. SE(3)-equivariant prediction of molecular wavefunctions and electronic densities. *NeurIPS* **34** (2021). [原始论文与作者](https://arxiv.org/abs/2106.02347)。

返回[分类导航](README.md)或[专题首页](../README.md)。
