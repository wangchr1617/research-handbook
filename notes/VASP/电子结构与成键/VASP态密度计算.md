# VASP 态密度计算

**适用环境：Windows、macOS、Linux（准备输入与绘图）；Linux + PBS（VASP、VASPKIT）。**

以两个原子的金刚石型硅原胞为例，计算总态密度和原子轨道投影。先完成结构优化，再在固定结构上使用较密的均匀 k 点做静态计算。

## 准备与提交

案例提供 [POSCAR](../../../examples/vasp/minimal/density-of-states/POSCAR)、[INCAR](../../../examples/vasp/minimal/density-of-states/INCAR)、[KPOINTS](../../../examples/vasp/minimal/density-of-states/KPOINTS)、[POTCAR.spec](../../../examples/vasp/minimal/density-of-states/POTCAR.spec)、[job.pbs](../../../examples/vasp/minimal/density-of-states/job.pbs) 及[后处理入口](../../../examples/vasp/minimal/density-of-states/analyze.py)。

按 `POTCAR.spec` 从授权势库准备 Si 势；VASPKIT 中可用 `104` 显式选择元素势。`102` 可生成均匀 k 网格。本例采用 $5\times5\times5$ Γ 中心网格，目的是快速走通 DOS 流程；正式 DOS 应加密网格并比较峰形与带边。

`INCAR` 中的关键设置为：

```text
IBRION = -1
NSW = 0
ISMEAR = -5
LORBIT = 11
NEDOS = 401
```

`LORBIT=11` 输出原子与轨道投影，`NEDOS` 决定能量网格的点数，并不替代 k 点收敛。四面体积分需要合适的三维 k 网格，不能直接用于仅有 Γ 点的分子或大超胞计算。

在集群加载 VASP、MPI 和 VASPKIT 环境后，执行 `qsub job.pbs`。

## 用 VASPKIT 提取

作业脚本先检查 VASP 是否完成电子自洽，再调用 VASPKIT `111`，写出 `TDOS.dat` 与 `ITDOS.dat`。对应操作保存在 [vaspkit.in](../../../examples/vasp/minimal/density-of-states/vaspkit.in)，也可在结果目录手动运行：

```bash
vaspkit < vaspkit.in
```

需要分元素或原子投影时，可分别选择 `113` 或 `112`；用 `115` 选择特定原子和轨道。菜单与投影列以当前版本输出为准，相关说明见 [VASPKIT 教程](https://vaspkit.com/tutorials.html)。

绘图前检查能量参考：VASPKIT 通常按配置将费米能置零。半导体比较不同结构时可改用价带顶等统一基准；不要把各自置零的曲线当成绝对能级对齐。PDOS 是特定投影定义下的结果，原子与轨道投影之和不一定严格等于总 DOS。

## 结果图

后处理会调用 [plot.py](../../../examples/vasp/minimal/density-of-states/plot.py) 绘图。已有提取数据时，在结果目录单独执行 `python3 plot.py` 即可重画，无需重算 VASP；绘图依赖见 [requirements.txt](../../../examples/vasp/minimal/density-of-states/requirements.txt)。

![硅原胞总态密度，PBE、5×5×5 k 网格；虚线为该 DOS 计算的费米能。](../assets/si-dos.png)

硅原胞总态密度，PBE、5×5×5 k 网格；虚线为该 DOS 计算的费米能。

## DOS 小峰与陷阱态怎样区分

带边附近多出一个峰时，先检查离散本征值、占据、自旋、k 点和展宽，确认它不是采样或绘图造成的结构。再比较相容参考下的完整体系与目标缺陷、吸附或取代模型，并查看该能窗中态的空间分布。

**PDOS 权重大，是否就说明电子局域在这个原子附近？** 权重只表示所选投影上的贡献，实空间局域性还要看态的空间分布。有限分子轨道 DOS 中的孤立小峰，也不能直接命名为周期材料的浅陷阱。

VASP 的 [LPARD 后处理](https://vasp.at/wiki/LPARD)可从已收敛的 `WAVECAR` 按能带或能窗输出部分电荷密度，选择入口为 `IBAND` 或 `EINT`，k 点选择另由 `KPUSE` 控制。保存实际能带、能窗、k 点、自旋及归一化约定，检查完整分布而不只看一个等值面；不同超胞还需比较局域范围和缺陷镜像耦合。该入口的实现限制以所用版本为准，当前官方说明不支持非共线计算。

判断陷阱深浅需明确相对带边的能量参考及所研究的是单粒子能级、垂直激发还是弛豫后的电荷态转变。局域态的出现不直接给出俘获率、释放时间、迁移率或电导；这些性质还涉及载流子占据、电子与晶格响应及相应动力学。仅凭一个小峰随温度展宽或靠近前线轨道，不能确定热调控导电机制。

## 与 UPS、XPS 对照时还需要什么

占据 DOS 可帮助归属价带光电子谱，但实验强度还受光子能量、光电离矩阵元、占据、表面敏感性、终态及展宽影响。XPS 也能测量价带，并非只对应芯能级。等权重展宽全部占据态得到的是简化谱形；按原子或轨道截面加权 PDOS 时，记录截面的光子能量与来源，以及投影和归一化约定。相关物理关系见[光电子谱与 DOS 的原始讨论](https://pmc.ncbi.nlm.nih.gov/articles/PMC6696543/)。

有限分子或团簇的垂直电离能是固定初态核坐标下、指定 N−1 电子终态与 N 电子初态的总能差；阴离子脱去电子时通常称垂直脱附能。把各占据轨道能量取负，再统一平移至第一电离能，只校准一个参考位置，不会自动修正较深电离态的相对间隔、弛豫或卫星峰。

周期材料的 DOS 采用其自身能量参考，不能直接对每个本征值取负就解释为相对真空的结合能；与费米能、价带顶或真空对齐的比较应分别说明，真空对齐见[功函数计算](../表面与反应/VASP功函数计算.md)。

作图保留原始能级与离散棒谱，记录能量平移、展宽函数、FWHM 和各态权重。改变线宽会改变重叠峰的高度与分辨程度，面积权重也不等于峰高；为贴合实验手动调整强度时，应明确为经验处理。

一张经过平移和展宽后吻合的曲线可支持结构候选，却不能独自唯一确定结构、磁态或价态，还需比较其它候选及独立证据。芯能级化学位移与价带 DOS 的归属是不同任务，应采用相应的芯空穴或其它经验证方法。
