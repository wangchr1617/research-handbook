# M3GNet

**适用环境：通用（原理）；运行接口按所用 MatGL / 模型版本准备。**

M3GNet 是从材料属性图网络走向可求力的通用材料势的重要代表。其核心是显式加入三体角度信息，学习总能，再对几何求导。

## 一、历史与开发团队

Chi Chen 与 Shyue Ping Ong 于 2022 年发表 M3GNet，来自 UC San Diego 的 Materials Virtual Lab。它在 MEGNet 等图网络工作的背景下，引入三体相互作用并利用 Materials Project 的结构弛豫数据训练通用势；软件生态随后也发展到 MatGL。[^paper][^code]

## 二、架构与学习对象

节点表示原子，边表示截断内原子对，角度关系连接共享中心的两条边。网络更新原子、键以及相关结构信息，输出总能。含角度的三体表示能够区分相同键长、不同键角的环境，优于只看径向距离的简单图表示。

它是势能模型，通常不输出轨道分辨的 $H_{i\alpha,j\beta}$。三体输入也不意味着整个深层模型只能表达三体函数，多层和非线性会产生更复杂依赖。

## 三体图到底如何产生

以一个中心 Si 和四个四面体邻居为例，普通原子图先记录四条中心–邻居边；用于三体关系的线图再连接共享中心的两条边，使角度进入边更新。每个中心有 $n$ 个邻居时，有序边对数量约为 $n(n-1)$，这解释了大 cutoff 或高密度环境下角图成本为什么增长很快。

网络中的“原子图截断”和“三体截断”可能不同。比较速度或精度时，必须分别记录，不能只写一个 5 Å。增加三体角度项可区分相同径向分布的局域环境，具体例子可对照[描述符案例](../../../examples/machine-learning/atomistic-models/descriptor_demo.py)。

## 三、特点与局限

M3GNet 的主要贡献包括跨元素预训练、材料弛豫和筛选工作流。数据库的广度降低了从零训练的门槛，但新材料、新相态与高温条件的准确性仍由数据覆盖决定。训练目标继承参考计算方法，不能把模型能量直接与任意另一套 DFT 总能拼接。

与 [CHGNet](CHGNet.md)相比，后者进一步用磁矩监督约束隐表示；与 [MACE-MP](MACE-MP与MACE-OFF.md)相比，表示路线和权重训练方式不同。相同任务下的对比才有解释力。

## 四、结果检查

先核对模型元素映射和能量单位，比较未参与训练决策的结构、力及弛豫路径；做材料稳定性研究时再检查相对能与参考相的一致口径。使用旧 TensorFlow 实现或 MatGL 实现时，分别记录包、权重和接口，避免只写“M3GNet 默认模型”。

## 实践：先区分属性预测器与势能模型

M3GNet / MatGL 生态既有形成能预测器，也有势能模型。形成能网络返回一个结构性质，不必满足对坐标求导后就是可用于 MD 的力。以官方形成能例子中的 CsCl 为例：

```python
from pymatgen.core import Lattice, Structure
import matgl
model = matgl.load_model("M3GNet-Eform-MP-2019.4.1")
cscl = Structure.from_spacegroup("Pm-3m", Lattice.cubic(4.1437),
                               ["Cs", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
eform = model.predict_structure(cscl)
print(float(eform), "eV/atom, formation-energy model")
```

该模型名与调用见[MatGL 官方示例](https://github.com/materialyzeai/matgl#model-usage)。它用于解释输出对象，不能将这个 `eform` 当作总势能，给结构优化器随意求导。模型是否仍可用需按对应软件版本与模型发布核对。

## 一个明确版本的势能模型调用

若要计算力而不是形成能，可采用模型卡明确给出的 MatPES 势，并用 ASE 接口：

```python
import matgl
from matgl.ext.ase import PESCalculator
from ase.build import bulk
potential = matgl.load_model("materialyze/M3GNet-PES-MatPES-PBE-2025.2")
atoms = bulk("Si", "diamond", a=5.43)
atoms.calc = PESCalculator(potential=potential)
print(atoms.get_potential_energy(), atoms.get_forces())
```

这套权重的[官方模型卡](https://huggingface.co/materialyze/M3GNet-PES-MatPES-PBE-2025.2)要求包含三体父边映射修正的 MatGL `d0b6bf0` 或后续提交，不能只按模型名称匹配一个任意旧安装。其三体 cutoff 为 4 Å、原子图 cutoff 为 5 Å；这正好说明三体图索引和模型权重必须与实现一致。

## 软件代际不能只看模型名字

MatGL 官方说明 3.0 代移除 DGL 后端并调整消息聚合约定，旧权重与新实现不能默认数值兼容。复现 2022 年论文时应保留对应历史实现与权重；使用新接口时则记录新模型发布与计算约定，不把两次结果都简写成“同一个 M3GNet”。

## 参考资料

[^paper]: C. Chen, S. P. Ong. A universal graph deep learning interatomic potential for the periodic table. *Nature Computational Science* **2**, 718–728 (2022). [原始论文](https://doi.org/10.1038/s43588-022-00349-3)。
[^code]: Materials Virtual Lab. [M3GNet](https://github.com/materialsvirtuallab/m3gnet)、[MatGL](https://github.com/materialyzeai/matgl)。

返回[分类导航](README.md)或[专题首页](../README.md)。
