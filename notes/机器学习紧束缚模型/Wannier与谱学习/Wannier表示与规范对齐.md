# Wannier 表示、降维与规范对齐

**适用环境：通用（原理）；实际文件按 Wannier90 所用版本读取。**

Wannier 方法把 Bloch 态组合成局域函数，从已有电子结构构造紧束缚表示。Wannier90 本身不是机器学习模型，但它可产生学习矩阵、构造低能模型及验证能带所需的数据。

## 一、历史与开发团队

Nicola Marzari 与 David Vanderbilt 在 1997 年建立最大局域 Wannier 函数路线；Arash A. Mostofi、Jonathan R. Yates、Young-Su Lee、Ivo Souza、Vanderbilt 和 Marzari 等开发 Wannier90，2008 年发表软件论文，后续由社区持续推进。这里区分物理表示、软件与在其之上建立的 ML 模型。[^mlwf][^w90]

## 二、把一组能带变成局域轨道

对选定能带子空间，示意定义

$$
|w_{n\mathbf R}\rangle=\frac1{N_k}\sum_{\mathbf k}
e^{-i\mathbf k\cdot\mathbf R}\sum_m
|\psi_{m\mathbf k}\rangle U_{mn}(\mathbf k).
$$

$U(\mathbf k)$ 混合同一子空间中的态，选择合适的混合可以得到更局域的函数。若需要从纠缠能带中选择子空间，还涉及解纠缠与能窗。减少轨道数是一种子空间建模决定，不只是文件压缩。

在所得正交 Wannier 基中，$H_{mn}(\mathbf R)=\langle w_{m0}|\hat H|w_{n\mathbf R}\rangle$，再 Fourier 求和得到 $H(\mathbf k)$。局域化使远距离块较小，有利于截断、学习与稀疏求解。

## 三、为什么每个构型分别 Wannier 化后不能直接拼标签

不同构型的独立最小化可能得到轨道交换、符号翻转或子空间内更一般的酉混合。能带都正确时，矩阵也可能不连续。例如两个轨道的 $U=\mathrm{diag}(1,-1)$ 会让非对角跃迁翻转符号，若直接混合训练，网络可能学到互相抵消的标签。

因此数据准备需要固定投影、轨道身份、能窗和相位，并用轨道重叠或连续追踪等方法对齐。存在近简并时，应关注子空间而非强行给单条态贴固定标签。规范问题的矩阵推导见[哈密顿量基础](../../机器学习哈密顿量/基础与比较/从轨道到哈密顿量矩阵.md)。

## 实践：用真实轨道矩阵看规范翻转

先运行[水分子矩阵案例](../../../examples/machine-learning/atomistic-models/molecular_matrix.py)，对七轨道空间构造 $U=\mathrm{diag}(1,1,-1,1,1,1,1)$，同时计算 $U^THU$ 与 $U^TSU$。本征值应不变，某些非对角元符号改变。这与不同 Wannier 计算中轨道相位翻转造成的标签跳变是同类代数问题。

沿连续构型匹配轨道时，可用重叠矩阵做最大匹配，再在选定子空间中做酉对齐。仅按轨道中心最近匹配不足以处理简并混合。对齐变换还要施加到位置、速度等相关算符上，否则电子谱不变而光学或拓扑响应改变。

## 四、读取文件与降维的边界

`seedname_hr.dat` 存储实空间矩阵及相关网格信息。读取时还需遵循所用版本的 Wigner–Seitz 简并权重、轨道索引、晶格和相位约定；不能只读若干跃迁数值就声称重现了原始插值。应先用文件重建参考能带，再用于机器学习。[^files]

更低能的模型可以通过投影或消去高能空间获得。将矩阵分块为低能 $L$ 和高能 $H$，消去高能系数可得能量依赖的有效矩阵：

$$
H_{\rm eff}(E)=H_{LL}+H_{LH}(E-H_{HH})^{-1}H_{HL}.
$$

具体步骤是从高能块方程求出 $c_H=(E-H_{HH})^{-1}H_{HL}c_L$，代回低能块方程。这个表达仅在逆存在时成立；在某个能窗把它近似成能量无关模型，是额外近似，不能认为任意固定小矩阵都能精确保持所有能带与响应。

## 五、结果检查

逐个构型先检查 Wannier 插值误差、中心和轨道身份，再检查相邻构型矩阵的连续性及厄米性。最终对独立构型和一般 $k$ 点验证。波函数相关物性还需同步变换位置、速度等算符，不能只对齐哈密顿量。

与只用能谱训练的模型比较见 [TBworks](TBworks与能谱监督.md)和[数据比较](../基础与比较/数据与横向比较.md)。

## 实践：读一个 hr 文件需要保留哪些字段

标准 `seedname_hr.dat` 的开头依次为注释、Wannier 函数数 `num_wann`、实空间网格点数 `nrpts`，再跟 `nrpts` 个简并权重，之后才是逐项矩阵数据。每行包含整数晶格位移、轨道索引、实部和虚部。索引通常从 1 开始，进入 Python 时要减一。

[SSH 案例](../../../examples/machine-learning/atomistic-models/fit_ssh.py)展示了按 $H_R$ 装配 $H(k)$ 的完整计算。真实 Wannier 文件的简并权重、Wigner–Seitz 映射与相位不能忽略；对旧版标准 hr 插值，常见求和含 $H_R/n_{deg}(R)$，但具体新版本若已应用权重，重复除一次就错了。

使用成熟读取工具，或先用同一份 hr 重建官方后处理能带，再接学习流程。仅通过 `np.loadtxt` 成功读取数字并不能验证格式解析正确。

## 一个可操作的材料数据验收顺序

以 Si 的 `sp3` 子空间为例，先固定投影与能窗，检查每个结构的目标带插值，再检查 Wannier 中心、展宽与轨道顺序，最后比较相邻热构型的跃迁连续性。若某帧子空间选择失败，先修正数据，不要让网络用平均化去掩盖规范跳变。

## 参考资料

[^mlwf]: N. Marzari, D. Vanderbilt. Maximally localized generalized Wannier functions for composite energy bands. *Physical Review B* **56**, 12847 (1997). [原始论文](https://doi.org/10.1103/PhysRevB.56.12847)。
[^w90]: A. A. Mostofi et al. wannier90: A tool for obtaining maximally-localised Wannier functions. *Computer Physics Communications* **178**, 685–699 (2008). [原始论文](https://arxiv.org/abs/0708.0650)。
[^files]: Wannier90 开发团队. [官方文档入口与版本说明](https://wannier.org/documentation/)。

返回[分类导航](README.md)或[专题首页](../README.md)。
