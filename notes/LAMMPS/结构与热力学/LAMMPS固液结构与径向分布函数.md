# LAMMPS 固液结构与径向分布函数

**适用环境：Linux + PBS（LAMMPS）；Windows / macOS / Linux 可绘图。**

径向分布函数 $g(r)$ 描述距参考粒子为 $r$ 的位置上出现其他粒子的相对概率。晶体有明显的壳层峰，液体通常保留近邻峰而远处相关减弱；结合 MSD，能更清楚地区分局部振动和持续扩散。

## 同密度的两个温度

[最小案例](../../../examples/lammps/minimal/solid-liquid-rdf)的 [in.lammps](../../../examples/lammps/minimal/solid-liquid-rdf/in.lammps)使用 256 个 LJ 粒子、约化密度 0.85，分别在 $T^*=0.2$、1.5 下独立初始化。每个温度先平衡 5000 步，再采样 5000 步，步长为 0.005。

```text
comm_modify cutoff 3.3
compute radial all rdf 80 cutoff 3.0
fix rdf_output all ave/time 10 50 500 c_radial[*] file rdf.solid.dat mode vector
```

计算在 0—3σ 范围分 80 个距离区间，每 500 步形成一个平均块。势的截止半径为 2.5σ；RDF 范围更大时，需要把通信距离扩展到 RDF 截断加邻居表 skin。增加 RDF 范围不意味着延长势的作用范围。

加载 LAMMPS，安装 [依赖](../../../examples/lammps/minimal/solid-liquid-rdf/requirements.txt)，提交 [PBS 作业](../../../examples/lammps/minimal/solid-liquid-rdf/job.pbs)：

```bash
qsub job.pbs
```

### 在 Alkemie 中采样

「最小化 → 平衡 → RDF 与均方位移」模板从三维周期的原子体系开始，完成平衡后在固定晶胞中另开 NVT 生产段。把生产温度设为平衡段的目标温度，生产步数取采样间隔的整数倍。组件沿用势函数的最大截断距离来计算全体原子的 RDF。体相算例宜检查此距离小于最短周期方向的一半。

`rdf.dat` 保存截至最后一个采样步的运行平均，每行依次为区间编号、距离、$g(r)$ 和累计配位数。`msd.dat` 保存步号、生产时间与去除质心漂移后的总 MSD。MSD 的参考坐标取自生产段起点。使用 `metal` 时，距离、时间和 MSD 的单位分别为 Å、ps 和 Å²。使用 `lj` 时，分别为 σ、τ 和 σ²。若要拟合扩散系数，另行选择长时线性区间并检查采样收敛。

### 用升降温观察结构转变

「升温熔化」与「降温凝固」组件在固定晶胞内使用 NVT 温度斜坡，沿用平衡末态的坐标和速度。升温从平衡晶体开始，降温先在高温得到平衡液体。将斜坡起点设为上游平衡段的目标温度，并依据积分步长和生产步数计算温度变化速率。

`phase.dat` 给出瞬时温度、每原子势能及五类共近邻分析（CNA）结构比例。`phase.lammpstrj` 保存带每原子 CNA 类型的轨迹。对单组分近密堆积体系，结合势能变化和 FCC/HCP 等比例判断结构转变。未识别类也包含晶界、缺陷或受热畸变的局部环境。截断距离要覆盖预期第一近邻壳层、避开下一壳层，并满足 CNA 的邻居通信要求。[LAMMPS compute cna/atom](https://docs.lammps.org/compute_cna_atom.html)

升降温速率、晶胞体积和超胞大小都会影响转变温度。报告观察到的转变时写明这些条件，并用 RDF 或轨迹复核结构变化。确定平衡熔点需要考察固液共存或计算自由能。

## 同时看结构与运动

[后处理](../../../examples/lammps/minimal/solid-liquid-rdf/postprocess.py)按实际行数解析 RDF 分块记录，平均十个采样块，并检查对应的 MSD 时间轴。[plot.py](../../../examples/lammps/minimal/solid-liquid-rdf/plot.py)绘图。

![低温与高温 LJ 体系的 RDF 和 MSD](../assets/solid-liquid-rdf.png)

低温曲线有清晰壳层峰，MSD 停留在约 0.02σ² 的振动尺度；高温峰形更宽，25 个约化时间后 MSD 约为 12.69σ²，表明粒子发生持续重排。OVITO 可进一步直观看轨迹，必要时结合结构识别和配位数。

这两个状态的比较不等于测出了熔点。连续加热可能出现过热，短时间内的晶体也可能仍被动力学困住；确定相变温度需更细温度采样、足够平衡和合适的共存或自由能方法。

LAMMPS 的标准 RDF 归一化基于全盒平均密度，适合这里的均匀体相。含大量真空的孤立团簇不能直接照搬相同的体相 $g(r)$ 解释。

参考：单斌、陈征征、陈蓉《计算材料学》配套仓库[第七章 7.11 体相熔化](https://github.com/stanfordbshan/CompMatBook/tree/main/edition-1-2023/Chapter07)；[LAMMPS compute rdf](https://docs.lammps.org/compute_rdf.html)。本例用重新编写的 LJ 小模型演示 RDF/MSD 分析。
