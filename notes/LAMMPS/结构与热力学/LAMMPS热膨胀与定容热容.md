# LAMMPS 热膨胀与定容热容

**适用环境：Linux + PBS（LAMMPS）；Windows / macOS / Linux 可绘图。**

同一块 Cu 在 200、400 和 600 K 下，各跑一段 NPT 能看盒子怎样随温度变化。如果想从能量随温度的斜率估计定容热容，就要另做一组固定体积的对照。下面沿用仓库的六个独立状态，说明从哪些列拟合，以及为什么两组数据不能交叉使用。

## 一、从同一个晶胞分出 NPT 与 NVT

[最小案例](../../../examples/lammps/minimal/thermal-response)的 [in.lammps](../../../examples/lammps/minimal/thermal-response/in.lammps)使用 4×4×4 常规晶胞，共 256 个 Cu，晶格常数初值为 3.615 Å。需要 LAMMPS 随附的 `Cu_u3.eam`（[来源与准备方法](../../../examples/lammps/minimal/thermal-response/POTENTIALS.md)）。加载软件时可设置 `LAMMPS_POTENTIALS` 指向势目录，或把势文件放到计算目录。

```text
fix bath all npt temp 400 400 0.1 iso 0 0 1.0
```

此为 400 K、目标压力 0 bar 的 NPT 设置，温控与压控时间常数分别为 0.1、1 ps。NVT 对照改用 `fix nvt`，三个温度下都保持同一个初始体积。`fix npt/nvt` 已包含积分器，不再叠加 `fix nve`。

本例分别计算 200、400、600 K，每个状态先平衡 5 ps、再采样 10 ps，步长 1 fs。加载 LAMMPS，安装 [依赖](../../../examples/lammps/minimal/thermal-response/requirements.txt)，在干净目录执行 `qsub job.pbs`（[PBS 文件](../../../examples/lammps/minimal/thermal-response/job.pbs)）。

## 二、沿各自的约束提取斜率

线膨胀系数和定容热容分别为

$$\alpha_L=\frac1a\left(\frac{\partial a}{\partial T}\right)_p,
\qquad \frac{C_V}{N}=\left(\frac{\partial\langle E/N\rangle}{\partial T}\right)_V.$$

[后处理](../../../examples/lammps/minimal/thermal-response/postprocess.py)检查六个状态的时间轴、实际平均温度和 NVT 体积不变性，以实测温度拟合。能量采用动能与势能之和，而非只用势能。[plot.py](../../../examples/lammps/minimal/thermal-response/plot.py)绘图，误差条来自五个 2 ps 块的均值波动。

![Cu 的 NPT 热膨胀与 NVT 能量变化](../assets/cu-thermal-response.png)

该小模型在 200—600 K 的拟合给出 $\alpha_L\simeq1.72\times10^{-5}\ \mathrm{K^{-1}}$，固定体积的 $C_V/N\simeq2.997k_B$。后者接近经典谐振固体的 $3k_B$，但短轨迹、势函数与有限尺寸仍会影响结果；经典 MD 不包含低温量子冻结效应。

若想快速查混用了哪份数据，可先看三个 NVT 分支的体积是否都等于初始值，再看 NPT 分支是否在各温度分别达到平稳。拟合热容时，横轴用每段实测平均温度，纵轴用同段的每原子总能。如果把势能当成总能，就漏掉了动能随温度的贡献。

NVT 中还可用总能涨落交叉估计 $C_V=(\langle E^2\rangle-\langle E\rangle^2)/(k_BT^2)$。本例三个温度的涨落估计约为每原子 3.16、2.97、2.63 $k_B$，比能量斜率更依赖采样长度，不应据此宣称涨落热容已收敛。五个短块也未必充分独立，误差条不作为严格置信区间。

若研究定压热容 $C_p$，应分析焓及相应系综；不能把 NPT 的总能斜率直接标成 $C_V$。正式结果需延长平衡与采样、检查体积和压力稳定性，并验证所用势在目标温度范围的适用性。

## 三、把同一体积检查接到 Alkemie 输出

使用「最小化 → 平衡 → NPT 密度与体积」时，先将三维周期体系平衡到目标温度和压力，再设定生产步数、采样间隔和温压阻尼。生产步数取采样间隔的整数倍。阻尼按实际时间单位填写，`metal` 使用 ps，`lj` 使用 τ。各向同性控压适合按同一比例调整晶胞各方向的体相算例。

`npt-density.dat` 依次记录步号、生产时间、密度、体积、压力和温度。平均密度使用生产段采样点，并跳过零时刻的初始帧。固定粒子数和组成时，可用密度与体积的乘积核对质量一致性。计算热膨胀时，应比较多个温度下已平衡的平均体积，并用分块检查采样稳定性。

「NPT 热膨胀系数」从同一初始构型分别启动至少三个温度点，各温度点在同一目标压力下单独平衡和采样。`response.dat` 记录目标温度、实际平均温度与平均体积。组件以各点的实际平均温度拟合体积斜率，再除以平均温度对应的拟合体积，给出体积膨胀系数。等效线膨胀系数为其三分之一，可用于各向同性近似。跨越结构转变时，应按单相温区分别拟合。

参考：单斌、陈征征、陈蓉《计算材料学》配套仓库[第七章 7.6—7.7](https://github.com/stanfordbshan/CompMatBook/tree/main/edition-1-2023/Chapter07)；[LAMMPS npt/nvt](https://docs.lammps.org/fix_nh.html)。本例重新编写独立恒温状态的采样与分析。
