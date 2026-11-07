# 投影质心与 NOCV 密度分解

**适用环境：Windows、macOS、Linux；已有 ORCA、Multiwfn、numpy、scipy、scikit-image 和 matplotlib。批处理示例使用 Bash。**

本目录包含两个独立的小模型：孤立 Zn 的 D 投影用于检查能窗与谱质心；固定水二聚体用于检查冻结参考和 NOCV。前者不是金属表面模型，后者沿用[轨道成分与 CDA 案例](../../orca/minimal/orbital-dos-cda/README.md)的未优化 PBE0/def2-SVP 波函数。

## Zn 原子与 D 投影质心

把 [zn.xyz](zn.xyz)、[orca.inp](orca.inp)、四份 `zn-*.in` DOS 菜单和 [zn-matrices.in](zn-matrices.in)复制到独立工作目录。以下命令在该工作目录执行，软件名已可调用：

```bash
mkdir -p zn zn-dos-narrow zn-dos-wide zn-dos-short-narrow zn-dos-short
cp zn.xyz zn/structure.xyz
cp orca.inp zn/
(cd zn && orca orca.inp > orca.out)
(cd zn && orca_2mkl orca -molden > molden.log)
(cd zn && multiwfn orca.molden.input -silent < ../zn-matrices.in > matrices.log)
(cd zn-dos-narrow && multiwfn ../zn/orca.molden.input -silent < ../zn-narrow.in > run.log)
(cd zn-dos-wide && multiwfn ../zn/orca.molden.input -silent < ../zn-wide.in > run.log)
(cd zn-dos-short-narrow && multiwfn ../zn/orca.molden.input -silent < ../zn-short-narrow.in > run.log)
(cd zn-dos-short && multiwfn ../zn/orca.molden.input -silent < ../zn-short-wide.in > run.log)
```

Zn 为中性单重态，PBE/def2-SVP、`TightSCF`、单进程。核对其 30 电子和完整 31 AO/轨道空间。[zn-matrices.in](zn-matrices.in)导出带重叠矩阵的 `matrices.mwfn`，用于独立选择 D 壳层和重建投影。

菜单用 `l d` 选全部 10 个 D 型基函数，以 Mulliken 贡献构造 PDOS；`DOS_curve.txt` 第 3 列为这个片段的 PDOS。四个任务的区别如下：

| 菜单 | 积分窗口 / Ha | Gaussian FWHM / Ha |
| --- | --- | --- |
| [zn-narrow.in](zn-narrow.in) | `−1.0` 至 `0.8` | `0.02` |
| [zn-wide.in](zn-wide.in) | `−1.0` 至 `0.8` | `0.10` |
| [zn-short-narrow.in](zn-short-narrow.in) | `−0.4` 至 `−0.3` | `0.02` |
| [zn-short-wide.in](zn-short-wide.in) | `−0.4` 至 `−0.3` | `0.10` |

宽窗口中心均约 `−0.346950 Ha`；窄窗口的宽核中心约为 `−0.348832 Ha`，与窄核相差约 `0.0512 eV`。这项变化由窗口裁切引起，说明固定波函数的谱质心也可能随显示/积分设置改变，详见 [d 带中心](../../../notes/计算化学/d带中心的能窗、参考与比较.md)。

## 水二聚体 NOCV

先按[同几何 CDA 案例](../../orca/minimal/orbital-dos-cda/README.md)取得复合物和两片段的 Molden 与矩阵 MWFN。将它们复制到本工作目录，并按下表命名；全部文件属于同一水二聚体与片段计算，不能混用 Zn 的文件。

| 本工作目录文件名 | 前一案例中的文件 |
| --- | --- |
| `complex.molden.input` | 原水二聚体 Molden |
| `fragment-1.molden.input`、`fragment-2.molden.input` | `fragment-1/orca.molden.input`、`fragment-2/orca.molden.input` |
| `complex-matrices.mwfn` | `composition/complex.mwfn` |
| `fragment-1-matrices.mwfn`、`fragment-2-matrices.mwfn` | 两片段各自的 `fragment.mwfn` |

把 [nocv.in](nocv.in)复制到工作目录，然后运行：

```bash
mkdir -p nocv
(cd nocv && multiwfn ../complex.molden.input -silent < ../nocv.in > run.log)
```

菜单进入 `23`、读取两片段，使用 `-2` 从最终态正则轨道反解 Fock/KS，再导出完整 `NOCV.txt`。五份密度网格在相同 `46×27×27`、步距 `0.3 Bohr` 的局部盒中生成：

- `pair-1.cub`：第一对 NOCV 的密度贡献。
- `all-pairs.cub`：全部 24 个 pair 之和。
- `Pauli.cub`：冻结态减片段密度和。
- `orb_def.cub`：实际态减冻结态。
- `EDD.cub`：实际态减片段密度和。

最后导出的 `NOCV.mwfn` 保存 NOCV 系数、本征值及矩阵；其中“占据”是带符号的密度差本征值，不是普通电子态占据。要做后续普通波函数分析，应重新载入原复合物。能量近似与度量定义见 [NOCV 笔记](../../../notes/计算化学/NOCV的冻结参考、密度分解与能量近似.md)。

## 提取与重绘

Python 库沿用[共用读取与绘图依赖](../../orca/minimal/weak-interactions/requirements.txt)。从仓库根目录运行，替换实际工作目录和输出位置：

```bash
python examples/multiwfn/orbital-moments-nocv/analyze.py \
  --work-root /path/to/work --output-dir /path/to/output
python examples/multiwfn/orbital-moments-nocv/plot.py \
  --data /path/to/output/moments-nocv.npz \
  --moments-output /path/to/output/d-centre-window.png \
  --nocv-output /path/to/output/nocv-density.png
```

[analyze.py](analyze.py)从 AO 矩阵重建 D 投影，分别核对原生格点求和与有限窗口 Gaussian 的解析一阶矩。NOCV 部分独立构造冻结占据空间、变形密度矩阵和正交度量谱，检查全部 pair 重建及三种密度差的加和关系。

[moments-nocv.json](moments-nocv.json)保存模型、能窗、矩阵误差与科学量；[moments-nocv.npz](moments-nocv.npz)保存 Zn 曲线、NOCV 系数/本征值/近似能量、密度差矩阵和实际网格层。完整三维 Cube、波函数与运行日志留在工作目录，已有两份派生数据时可直接重绘。

图中的第一对本征值约为 `±0.138334`，最终态 Fock 近似的全部 pair 能量和约为 `−4.6446 kcal/mol`，与完整 EDA 的总相互作用能分开报告。密度图使用统一对称对数色标，保留实际截面和数值，不从颜色面积估算电子数。
