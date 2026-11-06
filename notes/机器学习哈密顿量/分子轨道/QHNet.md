# QHNet

**适用环境：通用（原理）；原论文主要验证分子数据。**

QHNet（Quantum Hamiltonian Network）在保持 SE(3) 等变性的同时，重新组织张量运算和通道，提高哈密顿量矩阵预测的效率。

## 一、历史与开发团队

Haiyang Yu、Zhao Xu、Xiaofeng Qian、Xiaoning Qian 和 Shuiwang Ji 在 ICML 2023 发表 QHNet，来自 Texas A&M 相关机器学习与材料研究合作。代码发布在 DIVELab 的 AIRS 库中。[^paper][^code]

## 二、架构设计重点

节点携带旋转表示已知的特征，利用邻域信息更新；不同于简单堆叠大量昂贵张量积的方案，QHNet 通过结构设计减少张量积数量，并控制多元素情况下的通道扩张，再映射为对应轨道块。

输出的大小由基组决定，不由“原子元素有多少种”单独决定。不同元素可能具有不同轨道数，输出掩码、元素对应的轨道布局和矩阵装配必须同步。具体模块与成本统计见原论文，论文中的降幅只针对其比较设置。[^paper]

## 三、它与势函数等变网络有什么不同

势函数最后只需一个旋转标量能量；QHNet 的输出要覆盖轨道对组成的矩阵块，具有更丰富的角动量变换。两者可以共享球谐、张量积等构件，但不能直接把 NequIP 的标量输出头换成任意矩阵就认为完成哈密顿量学习。

与 [PhiSNet](PhiSNet.md)的比较要固定基组、标签、数据划分和实际总耗时。减少张量运算并不保证端到端电子性质计算获得相同比例加速，因为本征求解可能成为瓶颈。

## 四、结果检查

先重现一个固定分子、固定基组的数据流程，验证轨道掩码、矩阵对称性和旋转等变，再比较矩阵误差及占据/未占据能级误差。原论文在若干 MD17 分子上验证，不应直接解释成对任意周期材料的成熟通用模型。

向晶体迁移还需要晶格位移、周期矩阵块、$k$ 空间装配和相应训练数据，见[周期体系导航](../周期体系/README.md)。

## 实践：读原始训练命令与网络版本

官方 AIRS 中的工作目录是 `OpenDFT/QHNet`。准备相应带矩阵标签的 MD17 数据后，原始单分子训练入口为：

```bash
python train_wH.py dataset=water model=QHNet_w_bias model.version=QHNet_w_bias
```

`water`、`ethanol`、`malondialdehyde` 和 `uracil` 是其示例任务名。命令及模型版本说明见[官方 readme](https://github.com/divelab/AIRS/blob/main/OpenDFT/QHNet/readme.md)。普通只有坐标、能量和力的 MD17 文件不自动包含哈密顿量标签，不能直接替换其数据文件。

作者分别保留带/不带标量 bias 的模型版本；主论文与后续补充实验的浮点精度和训练计划也不同。复现时把这三项一起记录：模型实现文件、`float32/float64` 与调度计划，不能只保留一个随机种子。

## 源码怎样筛选允许的耦合路径

其 `get_feasible_irrep` 逻辑可以概括为以下真实接口组合：

```python
import torch
with torch.serialization.safe_globals([slice]):
    from e3nn import o3
input_irrep = o3.Irrep("1o")
edge_irrep = o3.Irrep("1o")
allowed = list(input_irrep * edge_irrep)
print(allowed)  # 0e、1e、2e
```

原函数遍历各输入表示，筛掉目标表示集合不允许的通道，再给张量积构造指令和归一化系数。源代码见[`ori_QHNet_with_bias.py`](https://github.com/divelab/AIRS/blob/main/OpenDFT/QHNet/models/ori_QHNet_with_bias.py)。路径筛选降低不必要运算，但不改变输出必须覆盖对应轨道块的要求。

下游先以[水分子矩阵案例](../../../examples/machine-learning/atomistic-models/molecular_matrix.py)验证本征求解和电子数，再接真实 QHNet 输出，能把网络误差与矩阵后处理错误分开定位。

## 参考资料

[^paper]: H. Yu et al. Efficient and Equivariant Graph Networks for Predicting Quantum Hamiltonian. *ICML*, PMLR **202**, 40412–40424 (2023). [会议论文](https://proceedings.mlr.press/v202/yu23i.html)。
[^code]: DIVELab. [AIRS 官方代码库](https://github.com/divelab/AIRS)。

返回[分类导航](README.md)或[专题首页](../README.md)。
