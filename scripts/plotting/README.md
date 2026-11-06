# 绘图

MSD 单文件分量和多文件比较均使用 `plot_msd.py`，通过 `--columns` 指定零起始列号，并明确设置时间单位和换算系数。

```bash
python scripts/plotting/plot_msd.py msd.out --columns 1 2 3 --time-unit ps
python scripts/plotting/plot_msd.py MSD_1.dat MSD_2.dat --skiprows 1 --columns 4 --time-unit fs
```

## 文件

- [plot_dos_gpumd.py](plot_dos_gpumd.py)：绘制 GPUMD 的声子态密度。
- [plot_dos_vaspkit.py](plot_dos_vaspkit.py)：绘制 VASPKIT 输出的态密度。
- [plot_ev_data.py](plot_ev_data.py)：读取ev.txt文件中的数据并绘制能量-体积曲线。
- [plot_ev_nep.py](plot_ev_nep.py)：读取体积和DFT能量数据以及NEP能量数据，绘制能量-体积(EV)曲线，并标出能量最低点。
- [plot_expansion.py](plot_expansion.py)：根据输入的热力学数据文件生成晶格膨胀的相关图表，并保存为 PNG 图片。
- [plot_force_comparison.py](plot_force_comparison.py)：读取计算的力数据和损失数据，绘制DFT和NEP力的比较图，并计算训练集的RMSE。
- [plot_force_error.py](plot_force_error.py)：计算参考数据、DFT数据和NEP数据之间的力误差，并绘制误差的直方图和拟合的正态分布曲线。
- [plot_kappa_correlation.py](plot_kappa_correlation.py)：该脚本加载 HAC 数据并计算平均值，然后绘制 $\kappa^{in}$、$\kappa^{out}$ 和总 $\kappa$ 的相关性图。
- [plot_lammps.py](plot_lammps.py)：绘制 LAMMPS 热力学输出。
- [plot_loss_dp.py](plot_loss_dp.py)：绘制 DeePMD 训练损失。
- [plot_loss_nep.py](plot_loss_nep.py)：读取损失数据文件，并绘制每一代的损失函数变化图及其他指标的RMSE和误差分布图。
- [plot_msd.py](plot_msd.py)：绘制单文件分量或多文件总 MSD（依赖 NumPy、Matplotlib）。
- [plot_neb.py](plot_neb.py)：绘制 NEB 能量曲线。
- [plot_nep_parameters.py](plot_nep_parameters.py)：绘制 NEP 参数分布。
- [plot_optconv.py](plot_optconv.py)：从 VASP 输出文件中读取数据并生成能量收敛、力收敛和初始结构变化的图表。
- [plot_pca.py](plot_pca.py)：对结构描述符进行 PCA 分析及绘图。
- [plot_pdos.py](plot_pdos.py)：绘制分波态密度。
- [plot_phonon_band.py](plot_phonon_band.py)：绘制声子能带。
- [plot_rdf.py](plot_rdf.py)：绘制径向分布函数。
- [plot_rmse_dp.py](plot_rmse_dp.py)：该脚本用于绘制 DFT 与 DP 计算结果的能量和力的比较图。
- [plot_scfconv.py](plot_scfconv.py)：该脚本用于从VASP的OSZICAR文件中读取自洽步骤的能量变化，并绘制能量收敛图。
- [plot_tdos.py](plot_tdos.py)：绘制总声子态密度。
- [plot_thermal_conductivity.py](plot_thermal_conductivity.py)：计算并绘制热导率结果。
- [plot_time.py](plot_time.py)：绘制截断能与耗时关系（依赖 NumPy、Matplotlib）。
- [plot_upho.py](plot_upho.py)：绘制展开声子谱。
- [plot_virial_comparison.py](plot_virial_comparison.py)：加载数据并绘制DFT和NEP virial的比较图。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
