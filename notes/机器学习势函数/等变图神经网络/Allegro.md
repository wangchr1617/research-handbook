# Allegro

**适用环境：通用（原理）；大规模动力学需相容的并行 MD 接口。**

Allegro 保留等变张量表示，同时限制每个局域能量贡献读取的环境范围。它与 NequIP 的重要区别是：不依靠跨原子节点的多跳消息逐层扩大感受野。

同一份周期构型分别用单设备和多个子域求力时，最先要对照的是每个原子的输出。论文里的并行效率只有在这一步通过后，才值得用自己的算例复测。下面沿 GeTe 的教学场景区分局域信息范围、边界通信和物理精度。

## 一、从等变消息到严格局域

Albert Musaelian、Simon Batzner 等人在 2022 年发布预印本，2023 年于 *Nature Communications* 发表 Allegro。工作来自 Harvard 的 Boris Kozinsky / MIR 团队及 Bosch 等合作团队。它与 NequIP 有共同的研究背景，但采用不同的局域信息组织方式。[^paper]

## 二、局域张量更新能读到哪些邻居

以有向中心–邻居边为对象，网络维护边相关的标量和等变特征，用中心截断环境中的邻居信息反复做张量积和更新，最后读出能量贡献。多层张量耦合增加局域多体表达，但不把邻居在其自身远端邻域汇总的信息继续传回中心。

因此“严格局域”说的是局域能量表示的结构依赖范围，不是说只有两体相互作用，也不是说原子力只依赖以该原子为中心的一份能量。总力仍然来自 $-\nabla_i\sum_j\varepsilon_j$，与原子 $i$ 有关的其他中心能量项都要计入。

## 三、为什么有利于大规模并行

把体系切成多个空间子域后，每个设备需要相邻边界的 ghost 原子。多跳消息通常还涉及逐层同步；固定局域环境可以减少这类依赖，使域分解更直接。实际加速仍受 cutoff、密度、跨域边界比例和 MD 实现影响，不能把论文中的原子规模当作任意机器上的承诺。

## 四、与其他局域势的比较

| 方法 | 表示局域环境的方式 | 非线性来源 |
| --- | --- | --- |
| DP | 学习对称描述符 | 嵌入与拟合网络 |
| NEP | 径向展开、多体不变量 | 描述符参数与小网络 |
| Allegro | 局域等变特征耦合 | 多层张量积与标量网络 |

Allegro 的局域性适合大规模 MD 的工程需求，但同样需要检查长程静电、磁态和化学域外问题。等变性与短程近似分别约束“怎样旋转”和“读多远”，不能互相替代。

## 五、先对照单设备与多设备的同帧结果

先核对单设备与多设备在同一周期结构上的能量、力、应力，再改变域分解检查一致性；在截断附近移动原子，检查力是否平滑。速度报告写清求力、邻居表和通信是否计入。

官方实现见 [Allegro](https://github.com/mir-group/allegro)，本仓库的编译入口见 [NequIP 与 Allegro 的 LAMMPS 接口](../../NequIP/NequIP与Allegro的LAMMPS接口编译.md)。

### 从局域层设置读懂训练配置

完整输入见[Allegro 教程配置](../../../inputs/machine-learning/allegro-tutorial.yaml)。它沿用 NequIP 的数据和训练框架，但模型构造器变为 `allegro.model.AllegroModel`：

```yaml
training_module:
  model:
    _target_: allegro.model.AllegroModel
    l_max: 1
    num_layers: 2
    num_scalar_features: 64
    num_tensor_features: 32
    tp_path_channel_coupling: true
```

这些字段摘自完整配置。`num_layers=2` 表示两次局域张量更新，不能理解成邻居信息传了两个原子图跳数。`num_scalar_features` 与 `num_tensor_features` 分别控制两类通道；只增加标量宽度和提高角阶，计算与表达效果不同。

官方输入使用 aspirin 的 CCSD 相关数据。其 ZBL 项写为 `units: real`，表示 Å、kcal/mol 的单位体系；如果改用 eV 标签，应把 ZBL 也改为相容单位，而不是仅更改文件后缀或坐标。

```bash
nequip-train -cn allegro-tutorial.yaml trainer.accelerator=cpu trainer.max_epochs=2
```

数据模块会按其实现下载和切分教程数据。正式使用前核对模型、NequIP 与 Allegro 包版本；旧仓库模板中的 `allegro.model.Allegro` 和新配置中的 `AllegroModel` 不是可随意替换的同名函数。

### 用一帧 GeTe 检查边界力

可借用仓库 GeTe 声子案例的晶胞作为几何输入。运行前另准备适用的 Allegro 权重和相容接口，声子案例的 NEP 权重用于其原有计算。先由原胞构造足够大的超胞，使试验能覆盖实际的子域边界。固定同一份超胞构型，再分别用单进程和多个空间子域求力。 [几何输入](../../../examples/gpumd/nep-phonons/POSCAR)

域分解后，边界原子会通过 ghost 副本提供位置和类型，局域能量按归属汇总，对相关坐标的力还需正确归约。对比时按原子 ID 对齐力，再分别记录全体与靠近子域边界原子的最大差。

若总能一致而边界原子力异常，优先排查 ghost 贡献、原子类型映射和邻居表；若换不同子域形状就变，排查通信与截断。把同一构型做超胞复制也是检查周期计数的有效办法。一致性通过后，再固定硬件、精度、体系和步数，改变子域数测每步耗时。若目的是比较不同架构，先按同一参考数据检查目标物性，再对照性能。

### 参考资料

[^paper]: A. Musaelian et al. Learning local equivariant representations for large-scale atomistic dynamics. *Nature Communications* **14**, 579 (2023). [正式论文](https://doi.org/10.1038/s41467-023-36329-y)、[2022 年预印本](https://arxiv.org/abs/2204.05249)。

返回[分类导航](README.md)或[专题首页](../README.md)。
