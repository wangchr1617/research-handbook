# TBMaLT

**适用环境：通用（原理与框架）；实现基于 Python / PyTorch。**

TBMaLT 是 Tight-Binding Machine Learning Toolkit。它提供把 TB / DFTB 电子结构计算与机器学习连接起来的可微工具，不是一套装好后就覆盖所有材料的预训练权重。

## 一、历史与开发团队

A. McSloy、G. Fan、W. Sun、C. Hölzer、M. Friede、S. Ehlert、N.-E. Schütte、S. Grimme、T. Frauenheim 和 B. Aradi 于 2023 年发表 TBMaLT。原始合作来自 University of Warwick、University of Bremen 和 University of Bonn 等团队。[^paper]

## 二、框架包含哪些层次

输入结构和元素后，按相应模型读入参数与局域基，完成积分插值、矩阵装配、本征求解及必要的自洽步骤，输出性质。机器学习模块可以在这些环节中预测参数或短程修正，再由已有量子模型生成电子性质。

原论文讨论了 DFTB 层及 GFN1-xTB 哈密顿量接口等实现。软件的模块化意图是允许接入不同模型；是否包含某个方法、导数或设备支持，应按具体版本核对，不能从论文的框架目标推断所有功能已齐备。[^paper][^code]

## 三、为什么可微求解有价值

若目标损失是 $L$，模型参数为 $\theta$，计算链可以示意为

$$
\theta\longrightarrow(H,S)\longrightarrow
(c,\epsilon,q)\longrightarrow\text{性质}\longrightarrow L.
$$

自动微分或相应解析导数把损失变化传回参数，使训练可以利用能量、偶极等性质，而不只依赖逐元素矩阵标签。但本征向量在简并处的表示不唯一，自洽迭代也可能不稳定；保持计算图只是必要条件之一。

## 四、与 DFTBML 的关系

[DFTBML](DFTB与DFTBML.md)是一条具体参数化与学习方案；TBMaLT 是可以容纳不同方案的计算工具。比较时应写清是在比较求解器、训练策略，还是某套训练好的参数，避免把框架本身当作一个固定模型参加精度排名。

## 五、开始实践与结果检查

先选官方已支持的小体系与参数集，验证未训练基线；再只放开少量参数，比较自动导数与有限差分。逐步检查电荷守恒、SCC 收敛、总能分项和参数曲线，再增加环境依赖修正。

保留参数文件来源、许可、元素配对覆盖及单位。若缺少某对元素的参数，不能靠把元素编号映射到相近元素来补齐。入口见[官方仓库](https://github.com/tbmalt/tbmalt)。

## 实践：沿官方 CH4 / H2O 例子追踪真实对象

官方 [`example_01.py`](https://github.com/tbmalt/tbmalt/blob/main/examples/example_01/example_01.py)使用 `Geometry`、`OrbitalInfo`、参数 feed 和 `Dftb2`。开头的结构与轨道准备可摘为：

```python
from ase.build import molecule
from tbmalt import Geometry, OrbitalInfo
geometry = Geometry.from_ase_atoms([molecule("CH4"), molecule("H2O")])
shell_dict = {1: [0], 6: [0, 1], 7: [0, 1], 8: [0, 1]}
orbitals = OrbitalInfo(geometry.atomic_numbers, shell_dict, shell_resolved=False)
```

这里 `shell_dict` 用原子序数作键，用角动量壳层列表作值。H 是一个 s，C/O 是一个 s 加一组 p。CH4 与 H2O 原子数不同，批处理会涉及 padding；零值填充位置不能作为真实原子参与电荷损失。

## 哪些参数参与梯度计算

官方例子从 `SkFeed.from_database` 读入 Hamiltonian 和 overlap 的样条，再将样条系数加入优化器。其训练循环的核心是：

```python
# dftb_calculator、geometry、orbitals、targets、optimizer 先按官方完整例子构造
# 以下是循环摘录，不能脱离参数 feed 单独运行
for epoch in range(10):
    dftb_calculator(geometry, orbitals)
    loss = criterion(dftb_calculator.q_final_atomic, targets["q_final_atomic"])
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

这段展示的目标是原子电子占据/电荷相关量，而不是仅拟合势能。完整例子中存在用于扩展的未实现辅助函数，且直接访问了一些私有 feed 字段；学习接口时应检出对应源码版本，不把这些私有名当成长期稳定 API。

训练前先验证参数文件和基线 SCC 结果，再检查参数梯度与有限差分，并确认迭代状态在各步正确更新。自动微分成功返回一个数，不等于自洽误差已经小于训练目标精度。

## 参考资料

[^paper]: A. McSloy et al. TBMaLT, a flexible toolkit for combining tight-binding and machine learning. *Journal of Chemical Physics* **158**, 034801 (2023). [原始论文](https://doi.org/10.1063/5.0132892)。
[^code]: TBMaLT 开发团队. [官方介绍](https://github.com/tbmalt/tbmalt/blob/main/README.rst)。

返回[分类导航](README.md)或[专题首页](../README.md)。
