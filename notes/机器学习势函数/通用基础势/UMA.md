# UMA

**适用环境：通用（原理）；运行按 fairchem 与具体权重要求准备。**

UMA（Universal Models for Atoms）试图把分子、材料、催化等多个化学域放到同一模型家族中处理。多域模型首先要解决参考方法与任务条件不同的问题，不能只把更多结构混在一起。

## 一、历史与开发团队

Meta FAIR 及合作团队于 2025 年公开 UMA，主要作者包括 Brandon M. Wood、Misko Dzamba、Xiang Fu、Meng Gao、Muhammed Shuaibi、Luis Barroso-Luque 等，并有 Carnegie Mellon 合作者。论文提出跨域数据训练与模型缩放研究；具体权重随 fairchem 生态提供。[^paper][^code]

## 二、架构中的线性专家混合

UMA 的一个设计重点是 Mixture of Linear Experts（MoLE）。可以把若干专家理解为若干组线性变换，按条件组合成有效权重：

$$
W_{\rm eff}=\sum_e a_eW_e,\qquad
y=W_{\rm eff}x.
$$

这个式子只是说明线性权重可先混合再作用，不是完整 UMA 前向式。其动机是增大容量，同时控制实际推理成本；不能据此把 UMA 简化成普通线性回归。专家混合位于更完整的等变原子网络中。[^paper]

## 三、任务条件为什么重要

来自分子、无机材料和催化数据的计算方法可能不同，同一几何的目标能量也可能不同。多任务模型通过相应条件区分这些目标。使用时必须选择匹配的任务设置；具体 API 的任务、总电荷和自旋等参数按权重及版本文档核对，不能假定遗漏参数仍对应研究目标。

大数据和大参数量带来跨域迁移的机会，但未见元素组合、反应、电子态及极端条件仍可能超出训练分布。模型的公开可用性、权重访问方式和适用许可也应以具体发布内容为准。

## 四、与其他基础势怎样比较

与 [MACE-MP](MACE-MP与MACE-OFF.md)或 [MatterSim](MatterSim.md)比较时，先对齐参考理论与任务域，再比较准确性、数据需求和推理成本。不能把多任务模型切换到不同参考口径后的能量，与单任务模型的原始总能直接比较。

## 五、结果检查

记录完整权重名、软件版本、任务条件、元素和单位；对相同构型做能量–力一致性与目标物性检查。跨域使用尤其要保留按化学域划分的误差报告，防止整体平均掩盖某一类体系的失败。

## 实践：同一权重为何还要指定 task

下面采用 fairchem 官方接口，在已有模型访问权限的环境中运行。权重下载按发布要求处理，访问令牌保存在本机认证中，不写入脚本。

```python
from ase.build import bulk
from fairchem.core import pretrained_mlip, FAIRChemCalculator
predictor = pretrained_mlip.get_predict_unit("uma-s-1p2p1", device="cpu")
atoms = bulk("Si", "diamond", a=5.43)
atoms.calc = FAIRChemCalculator(predictor, task_name="omat")
print(atoms.get_potential_energy(), atoms.get_forces())
```

`omat` 对应无机材料任务，而 `omol` 面向分子，`oc20` 等面向相应催化数据。它们包含不同参考计算口径，不能为了选出更好看的结果随意切换。具体模型与任务配对见[官方快速开始](https://github.com/facebookresearch/fairchem#quick-start)。

## 电荷、自旋与任务口径要一起检查

给几何设置磁矩不必然等于给该版本模型提供了所需的总自旋条件；分子任务中的总电荷、spin 字段如何编码，需要按具体 predictor 的系统适配器核对。条件未传入时，模型无法凭相同几何辨认所有电子态。

若要将 UMA 能量用于材料形成能或凸包，所有端元、化合物和校正必须采用相容的 OMat 口径。不能拿该输出直接减去 Materials Project 的参考总能。对上述硅例子可复用[MACE 扫描脚本](../../../examples/machine-learning/atomistic-models/mace_silicon.py)的几何、有限差分和超胞检查，但需要在独立 fairchem 环境里替换 calculator，并重新记录权重与 task。

## 参考资料

[^paper]: B. M. Wood et al. UMA: A Family of Universal Models for Atoms (2025；预印本含后续修订). [原始论文与版本历史](https://arxiv.org/abs/2506.23971)。
[^code]: FAIR Chemistry. [fairchem 官方仓库与模型入口](https://github.com/facebookresearch/fairchem)。

返回[分类导航](README.md)或[专题首页](../README.md)。
