# 数据分析

原子对径向分布函数使用 `calculate_rdf.py`；`analyze_adf_radial_function.py` 处理 ADF 轨道径向函数，两者物理含义不同。其余脚本按文件开头说明选择。

## NEP 误差汇总

```bash
python scripts/analysis/calculate_rmse.py --directory calculations/nep
```

默认读取 `energy_train.out`、`force_train.out`、`virial_train.out`，可分别用 `--energy`、`--force`、`--virial` 指定相对于 `--directory` 的文件或绝对路径。能量为两列，力为预测和参考各三列，virial 为预测和参考各六列；附加列不参与计算。

能量和 virial 输入须已按原子数归一到 eV/atom，力为 eV/Å。脚本计算所有行与分量的 RMSE，再乘 1000，输出 meV/atom 或 meV/Å；不会再除以原子数，也不会把 virial 换成应力。缺文件、空数据、列不足或参与计算的数据含非有限数时，报错并返回非零退出码。

## 容量与 RDF 的输入条件

```bash
python scripts/analysis/calculate_capacity.py structures Li 1 -o capacity.csv
python scripts/analysis/calculate_rdf.py topology.tpr trajectory.xtc --select-a 'name OW' --rmax 10 -o rdf.txt
```

容量脚本的位置参数依次是结构目录、阳离子名称（可多个）、每个输入晶胞转移的阳离子数。默认电荷为 Li/Na/K 的 +1、Mg/Ca 的 +2、Al 的 +3，其他电荷用 `--charge 元素=电荷` 指定。按输入晶胞质量用 `Q = n z F / (3.6 M)` 计算 mAh/g，不再推定所有元素为 +1、B 为 −2；相同化学式的不同结构按源文件名分别记录，不相互覆盖。`battery_capacity.py` 则是基于指定氧化态的独立模型库，要求电中性，不能用计量容量直接证明可插入量或电压。

RDF 的 `--select-a`、`--select-b`、`--rmax`、`--nbins` 与帧范围均可配置。全盒均匀体系使用 `--norm rdf`，半径应小于各采样帧周期盒最小面间距的一半。空间局部选区的几何归一化需另外建立；动态选区仅接受同一选择表达式配合 `--updating --norm none`，输出每帧壳层计数，不解释为无量纲的体相 RDF。相同组显式排除自配对，不再人为清零第一个 bin。归一化定义见 [MDAnalysis InterRDF 文档](https://docs.mdanalysis.org/stable/documentation_pages/analysis/rdf.html)。

## 文件

- [analyze_energy_data.py](analyze_energy_data.py)：比较 NEP 与 DFT 能量，按标准差排序并绘图。
- [battery_capacity.py](battery_capacity.py)：按指定氧化态与电荷平衡假设估算阳离子移除、插入量及容量。
- [birch_murnaghan_fitting.py](birch_murnaghan_fitting.py)：读取 `ev.csv` 中的晶格常数与能量，用 Birch–Murnaghan 方程拟合并绘图。
- [bondlengths_distribution.py](bondlengths_distribution.py)：根据共价半径构造邻居列表，汇总键长分布。
- [calculate_para_diffs.py](calculate_para_diffs.py)：比较训练集中能量、力与 virial 的偏差。
- [calculate_rdf.py](calculate_rdf.py)：该脚本用于计算指定区域内 A-B 原子对的径向分布函数（RDF）。
- [calculate_rmse.py](calculate_rmse.py)：按能量、力和 virial 的预测/参考分量计算 RMSE。
- [calculate_capacity.py](calculate_capacity.py)：读取结构与阳离子参数，按脚本中的氧化态假设计算比容量并保存 `capacity.csv`。
- [cohp_analysis.py](cohp_analysis.py)：从 `COHPCAR.lobster` 提取指定轨道对的 COHP 与 ICOHP。
- [get_max_rmse_xyz.py](get_max_rmse_xyz.py)：查找并导出误差较大的结构。
- [get_pairs.py](get_pairs.py)：按元素、距离范围和能量窗口生成 LOBSTER 输入。
- [pair_correlation_function.pl](pair_correlation_function.pl)
- [process_energy_data.py](process_energy_data.py)：从给定的 .xyz 文件中读取结构数据，并根据能量差异将其分类保存为两个不同的输出文件。
- [process_force_data.py](process_force_data.py)：从给定的 .xyz 文件中读取结构数据，并根据力差异将其分类保存为两个不同的输出文件。
- [analyze_adf_radial_function.py](analyze_adf_radial_function.py)：从 ADF 输出计算轨道径向函数，区别于原子对 RDF。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
