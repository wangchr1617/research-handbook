# 数据分析

原子对径向分布函数使用 `calculate_rdf.py`；`rdf_analysis.py` 处理 ADF 轨道径向函数，两者物理含义不同。其余脚本按文件开头说明选择。

## 文件

- [analyze_energy_data.py](analyze_energy_data.py)：读取 NEP 和 DFT 能量数据，计算每个结构的标准差，按标准差降序排列，选择和绘制指定范围内的数据。
- [analyze_forces_in_trajectory.py](analyze_forces_in_trajectory.py)：该脚本用于读取原子轨迹文件，计算每个结构的平均受力，并找出平均受力最大的结构和最小的结构。
- [battery_analysis.py](battery_analysis.py)：该脚本包含一组用于分析电池材料的方法，通过给定的氧化结构来评估其作为电池的潜力。主要功能包括计算在保持电荷平衡情况下可移除或插入的最大正离子数量，以及计算电池的最大容量。
- [birch_murnaghan_fitting.py](birch_murnaghan_fitting.py)：该脚本从ev.csv文件中读取晶格常数和能量数据，并使用Birch-Murnaghan方程进行拟合。拟合结果将生成一个散点图和拟合曲线，并保存为ev.png。
- [bondlengths_distribution.py](bondlengths_distribution.py)：该脚本读取结构文件（XYZ格式），计算所有键长，并生成键长分布的直方图。
- [calculate_cohesive_energy.py](calculate_cohesive_energy.py)：计算给定结构的晶胞体积并根据cohesive.out文件计算每个原子的能量。
- [calculate_distances.py](calculate_distances.py)：从XYZ文件中计算每个时间步内金原子(Au)的质心与各个金原子的距离，并将结果保存到文件中。
- [calculate_para_diffs.py](calculate_para_diffs.py)：比较训练集中能量、力与 virial 的偏差。
- [calculate_rdf.py](calculate_rdf.py)：该脚本用于计算指定区域内 A-B 原子对的径向分布函数 (RDF)。
- [calculate_rmse.py](calculate_rmse.py)：计算训练集中的能量、力和应力的均方根误差（RMSE）。
- [capacity_analysis.py](capacity_analysis.py)：该脚本从指定路径中读取结构文件，计算给定阳离子的最大重量比容量（mAh/g），并将结果保存为capacity.csv。
- [cohp_analysis.py](cohp_analysis.py)：从COHPCAR.lobster文件中提取选定的COHP和ICOHP数据。
- [get_max_rmse_xyz.py](get_max_rmse_xyz.py)：查找并导出误差较大的结构。
- [get_pairs.py](get_pairs.py)：#     指定起始和终止计算的能量，指定两种元素及其间的键长范围，生成Lobster输入文件。
- [pair_correlation_function.pl](pair_correlation_function.pl)
- [process_energy_data.py](process_energy_data.py)：从给定的 .xyz 文件中读取结构数据，并根据能量差异将其分类保存为两个不同的输出文件。
- [process_force_data.py](process_force_data.py)：从给定的 .xyz 文件中读取结构数据，并根据力差异将其分类保存为两个不同的输出文件。
- [rdf_analysis.py](rdf_analysis.py)：从 ADF 输出计算轨道径向函数，区别于原子对 RDF。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
