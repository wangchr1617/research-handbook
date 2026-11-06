# CHGNet

**适用环境：通用（原理）。**

CHGNet 的全称含 Crystal Hamiltonian Graph Neural Network，但其主要学习对象是势能、力、应力与局域磁矩，并非完整的轨道哈密顿量矩阵。它应首先放在机器学习势专题中理解。

## 一、历史与开发团队

Bowen Deng、Peichen Zhong、KyuJung Jun 等与 Gerbrand Ceder 团队于 2023 年发表 CHGNet，主要合作来自 UC Berkeley、Lawrence Berkeley National Laboratory 及相关合作者。模型使用 Materials Project 的轨迹数据，除了能量、力和应力，还引入局域磁矩监督。[^paper]

## 二、架构如何引入电荷相关信息

CHGNet 通过原子图、键和角度特征更新局域环境表示，并用磁矩预测任务约束中间原子特征。最终能量输出从经过约束的表示得到，力与应力关联能量对几何的导数。

为何磁矩有帮助？在部分过渡金属体系中，轨道占据、电荷态和局域磁矩相互关联，因此磁矩标签能为仅凭元素与几何难以区分的电子环境提供训练信息。但由磁矩推断氧化态需要化学前提，不能视为对任意材料唯一确定的真实电荷。[^paper]

## 三、与电子结构模型的边界

| 输出 | CHGNet 的定位 | 若需要更多信息 |
| --- | --- | --- |
| 能量、力、应力 | 势函数的主要任务 | 检查目标物性和数据域 |
| 局域磁矩与电荷相关表示 | 辅助监督和解释线索 | 核对定义、符号与适用化学环境 |
| 完整轨道矩阵、能带与波函数 | 不是名称所保证的输出 | 阅读[哈密顿量专题](../../机器学习哈密顿量/README.md) |

含磁矩标签不等于支持任意非共线磁序、显式自旋动力学或所有亚稳磁态。对同一几何存在多个电子态的问题，要核对模型是否能把它们作为不同输入处理。

## 四、结果检查

在训练域之外同时检查能量差、力与磁性相关量；不同磁序的相对稳定性应单独与参考计算比较。不能因为局域磁矩预测接近，就推断带隙或输运性质也正确。

实践入口与模型权重见[官方实现](https://github.com/CederGroupHub/chgnet)。模型选择及微调步骤见[通用势选型](通用势的预训练与选型.md)。

## 实践：Si 的原生预测与单位

以下使用 CHGNet 原仓库接口，并固定 `0.3.0` 权重名称。结构由 pymatgen 直接生成，避免额外 CIF 文件：

```python
from chgnet.model.model import CHGNet
from pymatgen.core import Lattice, Structure
structure = Structure.from_spacegroup("Fd-3m", Lattice.cubic(5.43),
                                      ["Si"], [[0, 0, 0]])
model = CHGNet.load(model_name="0.3.0", use_device="cpu")
prediction = model.predict_structure(structure)
print("eV/atom:", prediction["e"])
print("total eV:", prediction["e"] * len(structure))
print("forces shape:", prediction["f"].shape)
print("stress GPa:", prediction["s"])
print("magmom mu_B:", prediction["m"])
```

代码对应[CHGNet 官方用法](https://github.com/CederGroupHub/chgnet#direct-inference-static-calculation)。常规立方 Si 胞含八个原子，因此必须乘原子数才能与总能比较。`m` 是每个原子的磁矩相关预测；在 Si 上看到接近零的值，不意味着已验证过渡金属的电荷态预测。

## 以 LiMnO2 的应用为例解释磁矩监督

从同一参考计算获得能量、力、应力和局域磁矩，磁矩损失约束原子隐特征，能量头利用经过约束的特征预测总能。它不是先把模型预测磁矩强行变成整数价态，再用一个经验公式算能量。

若比较不同 Li 含量或 Mn 局域环境，先核对原始磁矩定义、参考磁序和 DFT+$U$，再检查局域结构–磁矩变化与相对能。不能把某个磁矩数值机械四舍五入成对所有体系有效的氧化态标签。

## 参考资料

[^paper]: B. Deng et al. CHGNet as a pretrained universal neural network potential for charge-informed atomistic modelling. *Nature Machine Intelligence* **5**, 1031–1041 (2023). [原始论文](https://doi.org/10.1038/s42256-023-00716-3)。

返回[分类导航](README.md)或[专题首页](../README.md)。
