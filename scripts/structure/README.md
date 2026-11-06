# 结构与训练集处理

优先选择以下通用入口：

- `convert_structure.py`：CIF、POSCAR、XYZ、XDATCAR 等格式转换，支持晶胞补充、扩胞、排序与固定晶胞轨迹解包裹。
- `vasp2xyz.py`：递归读取 VASP 结果，选择最后一帧或所有帧，显式筛选电子收敛并导出 extxyz。
- `xyz_grouped.py`：按元素或 z 坐标范围分组，保留其他原子属性。
- `xdatcar_slice.py`：指定起止帧与采样间隔。
- `mcsqs_convert.py`：使用 ATAT 转换 SQS，不修改原始输入。

```bash
python scripts/structure/convert_structure.py cell.cif POSCAR --sort-elements
python scripts/structure/vasp2xyz.py calculations -o train.xyz --frames all --converged
python scripts/structure/xyz_grouped.py model.xyz grouped.xyz --species Ge=0 Te=1
```

含 `ML_LMLFF` 的计算会拒绝直接导出为纯 DFT 标签，避免混入力场预测帧。

训练集导出默认能量为 TOTEN 自由能，单位 eV；`--energy zero` 选择零温外推值。virial 按 ASE 应力乘以负体积换算为 eV；`--no-virial` 可明确省略。电子收敛筛选会核对帧数，不能提供 OSZICAR 时不要把未筛选结果称为已收敛训练集。

## 文件

- [calculate_atomic_centers.py](calculate_atomic_centers.py)：读取POSCAR文件并计算每种元素类型的原子中心位置。
- [calculate_bond_angle.py](calculate_bond_angle.py)：该脚本加载POSCAR文件并计算指定三个原子的键角。
- [combine_vasp_structures.py](combine_vasp_structures.py)：该脚本用于合并两个VASP文件中的结构，并将它们保存为一个新的VASP文件。
- [convert_structure.py](convert_structure.py)：结构/轨迹格式转换（依赖 ASE）。
- [cp2k2files.py](cp2k2files.py)：用 Multiwfn 转换 CP2K 重启结构，不执行计算。
- [cp2k2xyz.py](cp2k2xyz.py)：该脚本从指定目录读取 CP2K 输出文件，并将数据转换为 XYZ 格式。
- [cp2k_pos_simplify.py](cp2k_pos_simplify.py)：从CP2K输出文件中每隔指定间隔提取原子结构数据，并保存到新的XYZ文件中。
- [create_structure.py](create_structure.py)：使用ASE库创建一个晶体结构并将其保存为VASP文件格式。
- [dp2ase.py](dp2ase.py)：将 DeepMD NumPy 数据集转换为 ASE 数据库（依赖 dpdata、ASE）。
- [dp2xyz.py](dp2xyz.py)：将 DeepMD 数据集转换为 XYZ/NEP 数据。
- [exchange_abatoms.py](exchange_abatoms.py)：在给定的POSCAR文件中，随机交换两个元素的原子位置，并将结果保存到新的文件中。
- [filter_atoms.py](filter_atoms.py)：该脚本从给定的轨迹文件中筛选出符合条件的结构，。
- [filter_xyz.py](filter_xyz.py)：过滤XYZ文件中的帧，删除不符合给定阈值条件的帧，并将结果保存到新的XYZ文件中。
- [gb_generate.py](gb_generate.py)：使用aimsgb库生成指定晶界方向和西格玛值的晶界结构，并保存为VAS文件格式。
- [gb_info.py](gb_info.py)：使用aimsgb库获取给定晶界方向和最大西格玛值的晶界信息。
- [gen_dimer.py](gen_dimer.py)：三端点分段线性插值，生成双原子拉伸等扫描结构（依赖 ASE）。
- [generate_random_perturbed_structures.py](generate_random_perturbed_structures.py)：根据给定的POSCAR文件生成具有随机晶格扰动的结构文件。
- [generate_random_structures.py](generate_random_structures.py)：从给定的结构文件生成随机扰动的原子结构，并将其保存到指定目录中。
- [get_bond_total.py](get_bond_total.py)：从POSCAR文件中读取结构数据，计算所有可能的原子对之间的距离，并输出结果。
- [idpp.py](idpp.py)：使用IDPP方法生成用于NEB计算的插值路径。
- [lattice_transformation_calculator.py](lattice_transformation_calculator.py)：读取POSCAR文件中的晶格参数，并计算原始单元格和基元单元格之间的转换矩阵。
- [mcsqs_convert.py](mcsqs_convert.py)：批量转换 ATAT SQS 输出。
- [pos_scaling.py](pos_scaling.py)：该脚本读取VASP的POSCAR文件，按指定的缩放因子对晶胞的c轴进行缩放，并生成相应的VASP文件。
- [rand_vacancy.py](rand_vacancy.py)：该脚本从VASP的POSCAR文件中随机删除指定数量的特定类型的原子，生成具有空位的结构，并保存为新的VASP文件。
- [random_atoms_generator.py](random_atoms_generator.py)：结构随机扰动算法模块，供 generate_random_structures.py 调用。
- [random_displacement.py](random_displacement.py)：对选定元素施加独立笛卡尔随机扰动（依赖 ASE、NumPy）。
- [remove_close_atoms.py](remove_close_atoms.py)：从XYZ文件中读取原子结构，删除距离小于给定阈值的原子对，并保存修改后的结构。
- [split_exyz.py](split_exyz.py)：该脚本用于分割EXYZ文件，选择指定范围或数量的帧，并输出选定的帧。
- [split_nep_data.py](split_nep_data.py)：该脚本用于将NEP格式的EXYZ数据集分成训练集和测试集。
- [supercell.py](supercell.py)：该脚本读取指定的VASP文件，并生成超胞结构。超胞结构的大小由输入参数[sx, sy, sz]指定。
- [vasp2dp.py](vasp2dp.py)：从多个系统中读取OUTCAR文件并将其转换为DeepMD格式数据。
- [vasp2xyz.py](vasp2xyz.py)：将 VASP 结果统一导出为训练用 extxyz（依赖 ASE、NumPy）。
- [xdatcar_slice.py](xdatcar_slice.py)：提取 XDATCAR 帧（依赖 ASE）。
- [xyz2dp.py](xyz2dp.py)：将 extxyz 训练集转换为 DeepMD NumPy 数据集。
- [xyz2exyz.py](xyz2exyz.py)：规范扩展 XYZ 的属性名并提取坐标、能量和力。
- [xyz_config_filter.py](xyz_config_filter.py)：按配置类型筛选 XYZ 帧。
- [xyz_force.py](xyz_force.py)：提取 XYZ 中的原子力并绘制分布。
- [xyz_grouped.py](xyz_grouped.py)：为 extxyz 增加整数 group 属性（依赖 ASE、NumPy），保留其他原子属性。
- [xyz_random.py](xyz_random.py)：从扩展 XYZ 文件随机抽取结构帧。
- [xyzfilter.py](xyzfilter.py)：按原子数过滤 XYZ 轨迹帧。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
