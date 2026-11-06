# NequIP

**适用环境：通用（原理）；LAMMPS 编译实践见已有 Linux CUDA 教程。**

NequIP 是等变图神经网络势的代表。它让原子携带标量、向量和高阶特征，通过邻居消息更新这些特征，最后输出旋转不变的原子能。等变性的基础见[入门推导](等变性与张量积入门.md)。

## 一、历史与开发团队

NequIP 于 2021 年发布预印本，2022 年发表于 *Nature Communications*。主要作者包括 Simon Batzner、Albert Musaelian 等，来自 Harvard 的 Boris Kozinsky / MIR 团队，与 Tess Smidt、Mario Geiger 及 Bosch 等合作者共同推进。早期预印本与正式论文在标题中的 SE(3)/E(3) 表述有所演进，引用时应明确版本。[^paper]

## 二、从原子图到总能

以元素嵌入初始化节点，以截断内原子对建边。第 $t$ 层读取邻居 $j$ 的 $h_j^{(t,l)}$，与边方向的球谐特征做张量积，再用径向网络产生的权重混合。节点汇总邻居消息，经过保持等变性的非线性和更新，形成下一层特征。

最后只从标量通道读出 $\varepsilon_i$，求和为 $E$，再求导得到力。中间层可以依赖方向，而最终能量不依赖整体方向，这两点并不矛盾。[^paper]

## 三、多跳传播与参数含义

若每层边长小于 $r_c$，$T$ 层理论上可沿图路径读到约 $Tr_c$ 范围的信息，实际依赖图连通性。这是有限跳数的传播范围，并非精确的无限长程相互作用。单个原子力依赖总能所有相关局域项，不能把特征半径、能量项半径和力的依赖范围混为一谈。

主要参数包括层数、通道数、$l_{\max}$、cutoff 和径向网络。更高角阶与更深网络增加表示能力，也增加显存、求导与跨域通信成本。

## 四、与 MACE 和 Allegro 比较

| 方法 | 特征构造重点 | 并行时关注 |
| --- | --- | --- |
| NequIP | 多层等变邻居消息 | 多跳传播与通信 |
| MACE | 显式高阶多体消息 | 相关阶、层数与成本 |
| Allegro | 固定局域环境中的张量耦合 | 严格局域性与域分解 |

这些结构差异不能直接推出某模型在所有体系都更准。NequIP 的数据效率表现来自原论文任务；迁移到液体、磁性体系或复杂界面仍需独立验证。

## 五、结果检查与实践入口

先做旋转检查与力的有限差分，再比较独立构型上的误差和短程 MD。训练、导出和 MD 插件应采用相容版本，不能把旧脚本的成功视为新版本接口已验证。官方实现见 [NequIP](https://github.com/mir-group/nequip)。仓库已有[NequIP 与 Allegro 的 LAMMPS 接口编译](../../NequIP/NequIP与Allegro的LAMMPS接口编译.md)，与这里的原理介绍配合阅读。

## 实践：读懂当前官方训练配置

完整输入见[NequIP 教程配置](../../../inputs/machine-learning/nequip-tutorial.yaml)，来源和接口快照见[输入说明](../../../inputs/machine-learning/README.md)。这是 Hydra / Lightning 风格的配置，不能与旧版 `model_builders` 配置直接混用。核心字段是：

```yaml
cutoff_radius: 5.0
num_layers: 4
l_max: 1
num_features: 32
training_module:
  model:
    _target_: nequip.model.NequIPGNNModel
    type_names: ${model_type_names}
    r_max: ${cutoff_radius}
    num_layers: ${num_layers}
    l_max: ${l_max}
    num_features: ${num_features}
```

这是完整输入中的结构摘录，不可单独覆盖整份配置。`_target_` 是 Python 构造器；`${...}` 是插值，只有一个源头控制 cutoff，避免数据邻居表半径与模型半径不一致。`num_features=32` 表示每种表示的通道重数，不是整个特征向量只含 32 个数。

以官方 `fcu.xyz` 教程数据为例，先按[官方数据脚本](https://github.com/mir-group/nequip/blob/main/configs/get_tutorial_data.py)准备文件，再在配置所在目录运行：

```bash
nequip-train -cn nequip-tutorial.yaml \
  trainer.accelerator=cpu trainer.logger=false trainer.max_epochs=2 \
  data.train_dataloader.num_workers=0
```

完整配置默认训练预算较大，此处两轮只检查数据、邻居图、前后向与保存流程，不代表收敛。真实科研数据应先按轨迹或结构家族划分，而不是沿用教程随机切分。每个 batch 拼成一个原子图：位置通常为 `[N_total,3]`，边索引为 `[2,N_edges]`，原子到结构的 `batch` 向量用于把原子能归约为各结构总能。

## 训练输出怎样检查

同时看验证的每原子能和力误差，核对 EMA 权重与部署时选用的权重是否一致。训练检查点、打包模型和用于特定 MD 接口的编译模型承担不同用途；导出后应在同一构型核对能量、力、应力，而非只检查文件存在。

在安装 NequIP 前，也可先运行[e3nn 案例](../../../examples/machine-learning/atomistic-models/equivariance_demo.py)，检查其最基本的张量积和旋转关系。

## 参考资料

[^paper]: S. Batzner et al. E(3)-equivariant graph neural networks for data-efficient and accurate interatomic potentials. *Nature Communications* **13**, 2453 (2022). [正式论文](https://doi.org/10.1038/s41467-022-29939-5)、[2021 年预印本及历史版本](https://arxiv.org/abs/2101.03164)。

返回[分类导航](README.md)或[专题首页](../README.md)。
