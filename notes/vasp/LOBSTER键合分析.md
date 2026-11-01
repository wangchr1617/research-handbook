# LOBSTER 键合分析

**适用环境：Linux + PBS（VASP 与授权 LOBSTER）；Windows / macOS / Linux 可查看结果图。**

LOBSTER 从平面波结果重建局域轨道投影。COOP 按重叠划分电子数，COHP 按哈密顿矩阵元划分单粒子能量，可帮助区分成键与反键贡献。

## 准备波函数

[硅近邻案例](../../examples/vasp/minimal/bonding-analysis/)提供 [POSCAR](../../examples/vasp/minimal/bonding-analysis/POSCAR)、[INCAR](../../examples/vasp/minimal/bonding-analysis/INCAR)、[KPOINTS](../../examples/vasp/minimal/bonding-analysis/KPOINTS)、[lobsterin](../../examples/vasp/minimal/bonding-analysis/lobsterin)和 [PBS 脚本](../../examples/vasp/minimal/bonding-analysis/job.pbs)。

用 `vasp_std` 做静态计算，输出 `WAVECAR`，并关闭空间对称约化。本例 `ISYM = -1`、`LWAVE = .TRUE.`、`NBANDS = 8`；能带数与两个 Si 的 `3s 3p` 局域基函数总数匹配。换元素时，按实际 PAW 数据和 LOBSTER 支持的局域基组重新选择，不能照搬大体系的 `NBANDS`。

保持结构、赝势、k 点与波函数来自同一次相容计算。已有 `WAVECAR` 是否可重用取决于这些设置，不需要一律删除；更换设置时宜使用新目录。

## 提交与分析

从[官网下载](https://schmeling.ac.rwth-aachen.de/cohp/index.php?menuID=6)取得适合系统的程序并阅读随包手册。准备授权 Si `POTCAR`，安装 [Python 依赖](../../examples/vasp/minimal/bonding-analysis/requirements.txt)，设置 `VASP_EXEC` 和 `LOBSTER_EXEC` 后提交：

```bash
qsub job.pbs
```

[run.py](../../examples/vasp/minimal/bonding-analysis/run.py)先运行 VASP，再以 OpenMP 方式启动 LOBSTER。也可使用 `--vasp-only` 分开执行两阶段。`lobsterin` 选择 Si 的 s、p 基函数和 2.0—2.6 Å 范围内的近邻键，输出 COHP 与 COOP；其关键词应与所安装版本的手册对应。

先看 `lobsterout` 中的警告和 charge spilling，再看键积分及能量分辨曲线。低 spilling 是必要检查之一，也应改变局域基组、VASP 数值精度和键选择，判断结论是否稳定。

[后处理脚本](../../examples/vasp/minimal/bonding-analysis/postprocess.py)核对非自旋数据布局、能量轴与电荷泄漏，并生成 `si-cohp.png`。图中绘制 −COHP：通常正值表示成键、负值表示反键，能量以费米能为零点。单键信息见 `ICOHPLIST.lobster`，不要把所有选定键的平均曲线解释为某一条特定键。

ICOHP 不等同于断键能或总能贡献，比较时应保持成分、基组、键定义与积分范围一致，见[官方 FAQ](https://schmeling.ac.rwth-aachen.de/cohp/index.php?menuID=3)。已有结果也可用 wxDragon 或 [LobsterPy](https://digimatchem.github.io/LobsterPy/)进一步分析。
