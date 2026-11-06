# HamGNN

**适用环境：通用（原理）；具体 DFT 接口、轨道与 SOC 支持按版本核对。**

HamGNN 是直接预测电子哈密顿量矩阵的等变图网络，可面向分子与固体。这里的“通用表示”首先指参数化形式可覆盖不同轨道块，不等于任意已训练权重都可跨所有材料使用。

## 一、历史与开发团队

Yang Zhong、Hongyu Yu、Mao Su、Xingao Gong 与 Hongjun Xiang 于 2023 年发表 HamGNN，来自复旦大学相关团队。后续发展包括新版本软件与通用 SOC 模型 Uni-HamGNN。应区分原始架构论文、软件版本和具体预训练模型。[^paper][^code]

## 二、从不可约张量到轨道块

网络利用元素与结构构造等变特征，把待预测轨道块分解成不同角动量和宇称的不可约球张量，再组合回哈密顿量矩阵。其核心与 [DeepH-E3](DeepH-E3.md)在表示思想上相关，但通道、网络与训练约定各自独立。

若涉及 SOC，还要处理自旋和时间反演约束。普通无自旋实矩阵的检查规则不能原样套到复数自旋矩阵上，详见 [SOC 与 Uni-HamGNN](../自旋与扩展/SOC与Uni-HamGNN.md)。[^paper]

## 三、迁移能力怎样理解

原论文测试了分子、同素异形体、化合物和更大结构的电子性质。小结构到大结构的迁移依赖局部化学环境和标签约定的一致，不是仅因为原子数更大就能保证成功。

例如训练集中都是中性、相近配位结构，若预测表面带电、强电荷转移或新磁序，局部几何相似也可能对应不同哈密顿量。数据范围、总电荷与磁态需要与用途一起记录。

## 四、使用时检查什么

| 阶段 | 关键检查 |
| --- | --- |
| 数据准备 | 基组、轨道顺序、实/复球谐、周期位移与单位 |
| 矩阵预测 | 厄米性、通道掩码、等变性与块误差 |
| 电子求解 | 重叠矩阵、电子数、能窗与费米能 |
| 应用 | 带隙、波函数相关量、拓扑或输运独立验证 |

模型构建矩阵的速度与后续电子求解速度应分开报告。与 [DeePTB-E3](DeePTB-E3与SLEM.md)比较时，还要看邻域依赖范围、局域装配与并行方案。

## 实践：V2 配置把学习对象写在哪里

配套[HamGNN V2 输入](../../../inputs/machine-learning/hamgnn-v2.yaml)对应官方 `examples/V2.x/config.yaml`。重要开关不只是网络宽度：

```yaml
output_nets:
  output_module: HamGNN_out
  HamGNN_out:
    ham_only: true
    ham_type: openmx
    nao_max: 19
    add_H0: true
    symmetrize: true
    soc_switch: false
setup:
  GNN_Net: HamGNNpre
  property: hamiltonian
  stage: fit
```

这是完整配置摘录。`ham_only=true` 不同时拟合 $S$；后处理仍要提供重叠。`nao_max=19` 是输出容量/轨道布局约定，不能因为自己的元素只用四轨道就任意删除掩码。`add_H0=true` 表示要按数据约定把基线矩阵加回；如果标签已经是完整矩阵又错误叠加一次，能谱会整体错误。

`loss_weight: 27.211` 与 Hartree–eV 换算尺度接近，但权重本身不证明数据已自动换成 eV。图生成器、基线项和评估单位都要按[官方实现](https://github.com/QuantumLab-ZY/HamGNN)核对。

## 一次完整运行需要什么

参考输出先通过相应 OpenMX / ABACUS 等接口生成 `graph_data.npz`，然后在已安装 V2 的环境执行：

```bash
HamGNN2.0 --config config.yaml > train.log 2>&1
```

正式运行时将 `graph_data_path` 指向实际文件，将 `setup.num_gpus` 改为硬件支持的值。完成后核对 epoch、验证误差和 checkpoint，再以 `stage: test` 及相应 checkpoint 配置推理，而不是直接拿训练时最后一个内存对象当作最佳模型。

## 用共同的后处理测试降低排错难度

先对一份参考矩阵运行[广义本征与电子数检查](../../../examples/machine-learning/atomistic-models/molecular_matrix.py)，再把输入替换为模型输出。对周期块还要检查负平移的共轭关系。`symmetrize=true` 只能处理相应对称关系，不能修复错误原子索引或不相容的轨道顺序。

## 参考资料

[^paper]: Y. Zhong et al. Transferable equivariant graph neural networks for the Hamiltonians of molecules and solids. *npj Computational Materials* **9**, 182 (2023). [原始论文](https://doi.org/10.1038/s41524-023-01130-4)。
[^code]: [HamGNN 官方实现](https://github.com/QuantumLab-ZY/HamGNN)、[官方方法介绍](https://hamgnn.readthedocs.io/en/latest/user_guide/introduction.html)。

返回[分类导航](README.md)或[专题首页](../README.md)。
