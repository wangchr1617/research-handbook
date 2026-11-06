# DeepH-E3

**适用环境：通用（原理）；适用于相应轨道与自旋表示的数据流程。**

DeepH-E3 把哈密顿量块拆成具有已知旋转规则的通道，让网络直接满足等变约束。它与原始 DeepH 的关系，是从局域坐标处理进一步走向全局等变表示。

## 一、历史与开发团队

Xiaoxun Gong、He Li 等与清华大学徐勇、段文晖团队及合作者于 2023 年发表 DeepH-E3，预印本于 2022 年公开。论文建立了包含 SOC 情况的 DFT 哈密顿量等变表示框架。[^paper]

## 二、矩阵块为什么能变成张量通道

左轨道角动量为 $l_i$、右轨道为 $l_j$ 时，一个矩阵块含 $(2l_i+1)(2l_j+1)$ 个分量。可以通过固定的角动量耦合，把它们重新排列为 $L=|l_i-l_j|,\ldots,l_i+l_j$ 的通道。

例如 $p$–$p$ 块有九个分量，分成 $L=0,1,2$ 后分别有 $1,3,5$ 个分量，合计仍为九个。这只是可逆地换一种表示，不是把九个数近似压成一个标量。网络预测这些通道，再用逆变换恢复矩阵块。更基础的例子见[等变性与张量积](../../机器学习势函数/等变图神经网络/等变性与张量积入门.md)。

## 三、架构特点与演进

等变图网络根据元素、径向和方向信息更新特征，输出符合轨道块变换规则的张量。宇称、不同径向副本和自旋结构都要按所用基与标签处理。相比依靠旋转增强学习输出规则，架构把一部分物理约束固定下来。[^paper]

原论文讨论了 SOC 和大尺度材料，但具体软件配置支持哪些轨道、自旋和参考接口仍需核对。旋转等变性也不等于对任意磁态、电子数或外场自动适用。

## 四、与 HamGNN 的比较

[HamGNN](HamGNN.md)同样将矩阵块与不可约张量表示联系起来。二者需比较数据接口、轨道约定、通道设计、输出约束、数据划分和实际速度；不能只看都使用 E(3) 就认为实现兼容。

## 五、结果检查

从无 SOC 的小结构开始验证矩阵与能带；旋转几何并同步变换轨道，检查等变关系。再增加 SOC、复数矩阵和自旋通道，检查厄米性与适用的时间反演关系。低能带分裂、近简并和拓扑量应单独评估。

实现入口可由 [DeepH-pack](https://github.com/mzjb/DeepH-pack)及论文代码声明追踪，采用与训练数据一致的版本与接口。

## 实践：使用原论文的配置与数据入口

[完整原始训练 INI](../../../inputs/machine-learning/deeph-e3-train.ini)保留 `basic/data/train/hyperparameters/target/network` 等节。它对应 [Xiaoxun-Gong/DeepH-E3](https://github.com/Xiaoxun-Gong/DeepH-E3)，不是后续重构软件的全部版本。

```ini
[target]
target = hamiltonian
target_blocks_type = all
[network]
cutoff_radius = 7.2
spherical_harmonics_lmax = 4
irreps_embed = 64x0e
irreps_mid = 64x0e+32x1o+16x2e+8x3o+8x4e
num_blocks = 3
```

`lmax=4` 是边方向展开的最高角阶；`num_blocks=3` 是交互块数，二者不能交换理解。该中间表示有 $64+32\times3+16\times5+8\times7+8\times9=368$ 个分量。比只写“高阶等变网络”更具体地看到了成本来源。

预处理数据目录要包含 `elements.dat`、`lat.dat`、`orbital_types.dat`、`site_positions.dat`、`info.json` 和 `hamiltonians.h5` 等文件。`orbital_types.dat` 记录的是角动量壳层列表：Mo 的 `[0,0,0,1,1,2,2]` 有七个壳层，但实际空间轨道数为 $3+2\times3+2\times5=19$，不能误读成七个轨道。

## 命令与标签规范的实际关系

```bash
python /path/to/DeepH-E3/deephe3-train.py train.ini
python /path/to/DeepH-E3/deephe3-eval.py eval.ini
```

训练脚本具体位置按所检出目录确认，以上按原项目命令入口说明，`eval.ini` 需要另按[官方默认评估配置](https://github.com/Xiaoxun-Gong/DeepH-E3/tree/main/deephe3/default_configs)准备。用原 DeepH 工具预处理时需设置 `local_coordinate=False`，因为模型学习全局等变表示，不能再套原始局域坐标变换。

参考数据由原论文 Zenodo 数据集提供，见[项目 README](https://github.com/Xiaoxun-Gong/DeepH-E3#usage)。只把 POSCAR 和一个训练 INI 放在目录中不够；没有轨道矩阵标签，无法监督训练哈密顿量。

## 参考资料

[^paper]: X. Gong et al. General framework for E(3)-equivariant neural network representation of density functional theory Hamiltonian. *Nature Communications* **14**, 2848 (2023). [正式论文](https://doi.org/10.1038/s41467-023-38468-8)、[预印本](https://arxiv.org/abs/2210.13955)。

返回[分类导航](README.md)或[专题首页](../README.md)。
