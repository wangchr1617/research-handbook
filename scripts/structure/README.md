# 结构与训练集处理

优先选择以下通用入口：

- `convert_structure.py`：CIF、POSCAR、XYZ、XDATCAR 等格式转换，支持晶胞补充、扩胞、排序与固定晶胞轨迹解包裹。
- `vasp_to_xyz.py`：递归读取 VASP 结果，选择最后一帧或所有帧，显式筛选电子收敛并导出 extxyz。
- `group_xyz.py`：按元素或 z 坐标范围分组，保留其他原子属性。
- `slice_xdatcar.py`：指定起止帧与采样间隔。
- `mcsqs_convert.py`：使用 ATAT 转换 SQS，不修改原始输入。

```bash
python scripts/structure/convert_structure.py cell.cif POSCAR --sort-elements
python scripts/structure/vasp_to_xyz.py calculations -o train.xyz --frames all --converged
python scripts/structure/group_xyz.py model.xyz grouped.xyz --species Ge=0 Te=1
```

含 `ML_LMLFF` 的计算会拒绝直接导出为纯 DFT 标签，避免混入力场预测帧。

训练集导出默认能量为 TOTEN 自由能，单位 eV；`--energy zero` 选择零温外推值。virial 按 ASE 应力乘以负体积换算为 eV；`--no-virial` 可明确省略。电子收敛筛选会核对帧数，不能提供 OSZICAR 时不要把未筛选结果称为已收敛训练集。

## DeepMD 数据转换

```bash
python scripts/structure/deepmd_to_xyz.py train --type-map Ge Te -o train.xyz
python scripts/structure/deepmd_to_ase.py train Ge Te -o train.db
python scripts/structure/xyz_to_deepmd.py train.xyz -o deepmd-data --set-size 2000
```

两个 DeepMD 读取入口处理全部 `set.*` 分片，校验原子数、元素映射、能量和力的形状及有限性。`type_map.raw` 缺失时须显式提供元素顺序；标签缺失时终止，不补造零能量或零力。ExtXYZ 保留 `nopbc` 与可选 virial，单位为 eV、eV/Å 和 eV；数据库中的应力按 `stress = -virial / volume` 换算。输入格式与字段定义见 [dpdata API](https://docs.deepmodeling.com/projects/dpdata/en/stable/api/dpdata.html)。

输出文件或目录必须不存在。DeepMD 输出目录先在临时位置生成，完成后再发布；`deepmd_to_xyz.py` 默认输出 `XYZ/DEEP2XYZ.xyz`，建议通过 `-o` 明确文件名。旧版 NEP `train.in` 可用 `--format nep --nep-version 1|2|3` 导出，版本 2 的全局元素索引顺序会打印到终端；非周期体系使用 ExtXYZ。

## 快速扩胞

保留简短的位置参数入口，三个倍数分别对应 a、b、c 晶格方向：

```bash
python scripts/structure/build_supercell.py POSCAR 2 2 1
python scripts/structure/build_supercell.py inputs/POSCAR 2 2 1 -o supercell.vasp
```

默认输出在输入文件所在目录，例如 `POSCAR_SC221.vasp`；`-o` 可指定其他文件。输出按元素排序，采用 VASP Direct 坐标，保留原晶胞的倾斜几何。倍数必须是正整数，已有文件和软链接均不覆盖。需要格式转换、晶胞补充或轨迹处理时使用上方的 `convert_structure.py`。

## 文件

- [calculate_bond_angle.py](calculate_bond_angle.py)：读取 POSCAR，计算给定三个原子的键角。
- [combine_vasp_structures.py](combine_vasp_structures.py)：合并两个 VASP 结构并保存为 `AB.vasp`。
- [convert_structure.py](convert_structure.py)：结构/轨迹格式转换（依赖 ASE）。
- [convert_cp2k_structure.py](convert_cp2k_structure.py)：用 Multiwfn 转换 CP2K 重启结构，不执行计算。
- [cp2k_to_xyz.py](cp2k_to_xyz.py)：读取 CP2K 的位置、力与晶胞输出，转换为扩展 XYZ。
- [deepmd_to_ase.py](deepmd_to_ase.py)：将 DeepMD NumPy 数据集转换为 ASE 数据库（依赖 dpdata、ASE）。
- [deepmd_to_xyz.py](deepmd_to_xyz.py)：将 DeepMD 数据集转换为 XYZ/NEP 数据。
- [exchange_atom_species.py](exchange_atom_species.py)：读取 POSCAR，随机交换两种元素的位置并写出结构。
- [generate_grain_boundary.py](generate_grain_boundary.py)：使用 aimsgb 按方向和 Σ 值生成晶界结构。
- [inspect_grain_boundary.py](inspect_grain_boundary.py)：使用 aimsgb 查询给定方向和最大 Σ 值对应的晶界信息。
- [generate_dimer_scan.py](generate_dimer_scan.py)：三端点分段线性插值，生成双原子拉伸等扫描结构（依赖 ASE）。
- [generate_random_perturbed_structures.py](generate_random_perturbed_structures.py)：从 POSCAR 生成晶格长度与角度受扰动的结构。
- [generate_random_structures.py](generate_random_structures.py)：调用随机结构模块，对给定骨架生成带约束的扰动结构。
- [get_bond_total.py](get_bond_total.py)：读取 POSCAR，汇总周期边界下的原子对距离。
- [generate_neb_path.py](generate_neb_path.py)：使用 IDPP 方法生成 NEB 初始插值路径。
- [lattice_transformation_calculator.py](lattice_transformation_calculator.py)：读取 POSCAR 与原胞晶格，计算转换矩阵。
- [mcsqs_convert.py](mcsqs_convert.py)：批量转换 ATAT SQS 输出。
- [generate_vacancies.py](generate_vacancies.py)：读取 POSCAR，随机删除指定数量的目标元素原子，生成空位结构。
- [random_atoms_generator.py](random_atoms_generator.py)：结构随机扰动算法模块，供 generate_random_structures.py 调用。
- [random_displacement.py](random_displacement.py)：对选定元素施加独立笛卡尔随机扰动（依赖 ASE、NumPy）。
- [split_extended_xyz.py](split_extended_xyz.py)：按范围或指定数量抽取 EXYZ 帧。
- [split_nep_data.py](split_nep_data.py)：使用 PyNEP 读写，将 EXYZ 数据分为训练集和测试集。
- [build_supercell.py](build_supercell.py)：按三个正整数倍数扩胞，按元素排序并输出 VASP Direct 坐标。
- [vasp_to_deepmd.py](vasp_to_deepmd.py)：汇集多个 OUTCAR，输出 DeepMD raw 与 NumPy 数据。
- [vasp_to_xyz.py](vasp_to_xyz.py)：将 VASP 结果统一导出为训练用 extxyz（依赖 ASE、NumPy）。
- [slice_xdatcar.py](slice_xdatcar.py)：提取 XDATCAR 帧（依赖 ASE）。
- [xyz_to_deepmd.py](xyz_to_deepmd.py)：将 extxyz 训练集转换为 DeepMD NumPy 数据集。
- [group_xyz.py](group_xyz.py)：为 extxyz 增加整数 group 属性（依赖 ASE、NumPy），保留其他原子属性。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
