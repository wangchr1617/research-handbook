# SOC、磁性哈密顿量与 Uni-HamGNN

**适用环境：通用（原理）；需要复数矩阵和明确的自旋基约定。**

包含 SOC 后，轨道和自旋耦合，原来的无自旋矩阵需要扩展。先说明自旋块结构，再理解 DeepH-E3、HamGNN 和 Uni-HamGNN 所处理的约束。

## 一、矩阵为什么变成自旋块

若原来有 $B$ 个空间基函数，为每个基加入 $\uparrow,\downarrow$ 两个分量，就有 $2B$ 个基。按先全部上自旋、再全部下自旋排序，

$$
H=\begin{pmatrix}H^{\uparrow\uparrow}&H^{\uparrow\downarrow}\\
H^{\downarrow\uparrow}&H^{\downarrow\downarrow}\end{pmatrix}.
$$

厄米性要求两个对角块各自厄米，且 $H^{\downarrow\uparrow}=(H^{\uparrow\downarrow})^\dagger$。若采用逐轨道排列上下自旋，矩阵布局不同，需显式置换。

对单个轨道对的 $2\times2$ 自旋块，任意复矩阵都能展开为 $h_0I+h_x\sigma_x+h_y\sigma_y+h_z\sigma_z$，其中 $\sigma_a$ 是 Pauli 矩阵。这是四个基矩阵的线性组合，允许系数为复数；只有整个块自身厄米时，系数才均为实数。不能无条件把非对角原子块也当作独立厄米矩阵。

具体地，$I$ 是单位阵，$\sigma_x=\begin{pmatrix}0&1\\1&0\end{pmatrix}$、$\sigma_y=\begin{pmatrix}0&-i\\i&0\end{pmatrix}$、$\sigma_z=\begin{pmatrix}1&0\\0&-1\end{pmatrix}$。把线性组合逐项相加，得到

$$
\begin{pmatrix}a&b\\c&d\end{pmatrix}
=\begin{pmatrix}h_0+h_z&h_x-ih_y\\h_x+ih_y&h_0-h_z\end{pmatrix}.
$$

逐个元素对应即可求出 $h_0=(a+d)/2$、$h_z=(a-d)/2$、$h_x=(b+c)/2$ 和 $h_y=(c-b)/(2i)$。这说明展开覆盖全部四个复分量。若矩阵厄米，$a,d$ 为实数且 $c=b^*$，代入可直接检查四个系数均为实数。

## 二、SOC 与磁性不是同一个条件

常见原子型 SOC 示意为 $H_{\rm SOC}=\lambda\mathbf L\cdot\mathbf S$。$\lambda$ 的数值依赖角动量单位及实现约定。加入 SOC 并不必然打破时间反演；非磁体系可以保留时间反演，而磁序可将其打破。

在相容的自旋基、无磁且满足时间反演的情形下，可以检查相应形式的

$$
H(\mathbf k)=(I_B\otimes\sigma_y)H^*(-\mathbf k)
(I_B\otimes\sigma_y).
$$

此式采用每个轨道内排列上下自旋；若使用上一节的自旋分块排序，两个 $I_B\otimes\sigma_y$ 要换成 $\sigma_y\otimes I_B$。还需同步考虑轨道基在时间反演下的表示，复球谐基不能省略其轨道变换。因此应以具体基约定构造时间反演算符，而非机械套式。

## 三、方法演进与开发团队

DeepH-E3 在 2023 年提出包含 SOC 的等变 DFT 矩阵表示；复旦大学 Yang Zhong、Hongjun Xiang 等团队的 HamGNN 也讨论相关对称参数化。2026 年 Zhong、Rui Wang、Xingao Gong 和 Xiang 发表 Uni-HamGNN，目标是跨更广元素与材料学习 SOC 哈密顿量，属于由专用矩阵模型走向通用预训练的一步。[^deeph][^ham][^uni]

## 四、通用 SOC 权重仍需检查什么

SOC 标签与非 SOC 标签、参考基组和能量零点需要统一；训练材料覆盖不能代替对目标磁态的支持。几何输入模型若没有显式磁矩或磁态条件，不能自动区分同一结构的任意磁序。

对近简并、拓扑和自旋纹理问题，除了矩阵 MAE，还要检查关键带分裂、对称保护简并、波函数与目标拓扑量。若体系有磁性，不应强行投影到非磁时间反演约束。

## 五、学习检查

数清每个元素的空间轨道和自旋维数；写出两种自旋排序之间的置换；检查上下非对角块的共轭关系。能完成这些步骤后，再阅读具体模型的 SU(2)、双群和时间反演实现。进一步推导这些对称关系，需要相应的量子力学与群论基础。

## 实践：用一个 p 壳层构造 SOC 矩阵

在复球谐基 $m=-1,0,1$ 中，取 $\hbar=1$。$L_z=\mathrm{diag}(-1,0,1)$，升算符满足 $L_+|l,m\rangle=\sqrt{l(l+1)-m(m+1)}|l,m+1\rangle$，由此算出 $L_x=(L_++L_-)/2$、$L_y=(L_+-L_-)/(2i)$。自旋算符 $S_a=\sigma_a/2$。

```python
import numpy as np
lplus = np.array([[0., 0., 0.], [np.sqrt(2), 0., 0.], [0., np.sqrt(2), 0.]])
lx, ly = (lplus+lplus.T)/2, (lplus-lplus.T)/(2j)
lz = np.diag([-1., 0., 1.])
sx = np.array([[0., 1.], [1., 0.]])/2
sy = np.array([[0., -1j], [1j, 0.]])/2
sz = np.diag([1., -1.])/2
coupling = 0.2  # eV
h_soc = coupling*(np.kron(lx, sx)+np.kron(ly, sy)+np.kron(lz, sz))
assert np.allclose(h_soc, h_soc.conj().T)
assert np.allclose(np.linalg.eigvalsh(h_soc), [-0.2, -0.2, 0.1, 0.1, 0.1, 0.1])
```

这个六维矩阵采用“每个轨道内上下自旋”的顺序。两个 $j=1/2$ 态的能量为 $-\lambda$，四个 $j=3/2$ 态为 $\lambda/2$；它是单壳层 SOC 例子，不是材料的完整能带。

## Uni-HamGNN 的实际使用入口

官方项目在 `Uni-HamGNN` 目录提供预测脚本，命令形式为：

```bash
python Uni-HamiltonianPredictor.py --config Input.yaml
```

需要先准备发布要求的权重、轨道和结构信息；`Input.yaml` 与通用模型的输入约定不能直接用普通 V2 的 `config.yaml` 替代，入口见[官方说明](https://github.com/QuantumLab-ZY/HamGNN#8-introduction-to-and-usage-of-uni-hamgnn-universal-model)。推理后对复矩阵检查厄米性、基排序和 SOC 分裂，再讨论具体拓扑或磁性结论。

## 参考资料

[^deeph]: X. Gong et al. DeepH-E3 (2023). [论文](https://doi.org/10.1038/s41467-023-38468-8)。
[^ham]: Y. Zhong et al. HamGNN (2023). [论文](https://doi.org/10.1038/s41524-023-01130-4)。
[^uni]: Y. Zhong et al. A universal spin–orbit-coupled Hamiltonian model for accelerated quantum material discovery. *Nature Machine Intelligence* **8**, 403–414 (2026). [论文](https://doi.org/10.1038/s42256-026-01196-x)、[官方项目](https://github.com/QuantumLab-ZY/HamGNN)。

返回[分类导航](README.md)或[专题首页](../README.md)。
