# 分子轨道

**适用环境：通用（原理）；软件环境见各篇说明。**

沿 SchNOrb → PhiSNet → QHNet 阅读，理解分子矩阵输出、等变性与效率设计。

## 笔记导航

| 笔记 | 先看什么 |
| --- | --- |
| [SchNOrb](SchNOrb.md) | SchNOrb（SchNet for Orbitals）把预测对象从少量标量性质推进到原子轨道基下的哈密顿量与重叠矩阵，再通过本征求解恢复分子轨道信息。 |
| [PhiSNet](PhiSNet.md) | PhiSNet 关注如何在网络结构中保证分子旋转时输出按正确规则变化。 |
| [QHNet](QHNet.md) | QHNet（Quantum Hamiltonian Network）在保持 SE(3) 等变性的同时，重新组织张量运算和通道，提高哈密顿量矩阵预测的效率。 |

返回[专题首页](../README.md)。
