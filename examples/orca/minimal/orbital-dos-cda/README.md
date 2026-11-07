# 水二聚体的轨道成分、DOS 与 CDA

**适用环境：Windows、macOS、Linux；已有 ORCA、Multiwfn、numpy 和 matplotlib。批处理示例使用 Bash。**

本例复用[弱相互作用案例](../weak-interactions/README.md)的六原子水二聚体：PBE0/def2-SVP、中性单重态、O···O 为 `2.9 Å`，几何固定且未优化。两个水分别作为片段，演示轨道分区、DOS 展宽和片段轨道变换。方法见[轨道成分](../../../../notes/计算化学/轨道成分、基函数与空间分区.md)、[DOS](../../../../notes/计算化学/DOS的展宽、分区与空间分布.md)及 [CDA](../../../../notes/计算化学/CDA的片段轨道与电荷分解.md)。

## 工作目录与波函数

按原案例产生二聚体的 `orca.molden.input`，复制到独立工作目录，命名为 `complex.molden.input`。把本目录两份片段坐标、`orca.inp` 和全部 `.in` 菜单也复制到工作目录。以下命令都在该工作目录执行，软件名已在路径中。

```bash
mkdir -p fragment-1 fragment-2 composition cda \
  dos-002 dos-005 dos-ev dos-hirshfeld ldos
for i in 1 2; do
  cp "fragment-$i.xyz" "fragment-$i/structure.xyz"
  cp orca.inp "fragment-$i/"
  (cd "fragment-$i" && orca orca.inp > orca.out)
  (cd "fragment-$i" && orca_2mkl orca -molden > molden.log)
  (cd "fragment-$i" && multiwfn orca.molden.input -silent < ../matrices.in > matrices.log)
done
```

[fragment-1.xyz](fragment-1.xyz)、[fragment-2.xyz](fragment-2.xyz)直接保留复合物的两个原子块，没有独立优化或 ghost 中心。[orca.inp](orca.inp)使用相同 PBE0/def2-SVP、`TightSCF`、一个进程和 `512 MB` 最大核心内存设置。分别确认 ORCA 正常结束、各片段 10 电子、24 AO，再继续分析。

[matrices.in](matrices.in)将每个片段导出为 `fragment.mwfn`，同时包含密度与重叠矩阵。这些完整文件留在计算目录，后处理脚本从它们核对轨道空间与 AO→FO 变换。

## 轨道成分与 CDA

```bash
(cd composition && multiwfn ../complex.molden.input -silent < ../composition.in > run.log)
(cd cda && multiwfn ../complex.molden.input -silent < ../cda.in > run.log)
```

[composition.in](composition.in)先导出 `complex.mwfn`，再按原子 `1-3`、`4-6` 定义片段，输出全部轨道的 Mulliken 和 SCPA 片段成分及跨片段重叠项。[cda.in](cda.in)读取两份片段 Molden，保存 `coFO.txt`、`ovlpint.txt`，并正常返回主菜单。

前一个水 A 对 HOMO 的 Mulliken/SCPA 成分约为 `99.7624%`/`99.7371%`，对 LUMO 为 `8.7962%`/`5.9099%`。CDA 的 \(d-b\) 约为 `−0.044171`，ECDA 的 A→B 净项约为 `−0.05391`；按定义分别报告，不能当作两种等价电荷读数。

## DOS、分区与单点 LDOS

```bash
(cd dos-002 && multiwfn ../complex.molden.input -silent < ../dos-narrow.in > run.log)
(cd dos-005 && multiwfn ../complex.molden.input -silent < ../dos-wide.in > run.log)
(cd dos-ev && multiwfn ../complex.molden.input -silent < ../dos-ev.in > run.log)
(cd dos-hirshfeld && multiwfn ../complex.molden.input -silent < ../dos-hirshfeld.in > run.log)
(cd ldos && multiwfn ../complex.molden.input -silent < ../ldos.in > run.log)
```

菜单针对 Multiwfn 2026.7.15，`-silent` 跳过自动图窗，保留导出。各目录采用同一波函数，含义如下：

| 目录与菜单 | 数据与条件 |
| --- | --- |
| `dos-002`：[dos-narrow.in](dos-narrow.in) | Mulliken PDOS/OPDOS，Gaussian FWHM `0.02 Ha`，窗口 `−1.5` 至 `1.5 Ha` |
| `dos-005`：[dos-wide.in](dos-wide.in) | 仅将 FWHM 改为 `0.05 Ha` |
| `dos-ev`：[dos-ev.in](dos-ev.in) | 相同窄核的 eV 表示，FWHM `0.544227676 eV`，窗口同步换算 |
| `dos-hirshfeld`：[dos-hirshfeld.in](dos-hirshfeld.in) | Hirshfeld 原子分区汇总成两个完整水，窄核，无 OPDOS |
| `ldos`：[ldos.in](ldos.in) | 坐标 `(2.7,0,0) Bohr` 的 LDOS，窄核 |

Ha 任务把曲线比例设为 `1`；eV 任务在单位切换后显式设置比例 `27.2113838`，补偿该版本内部轨道强度的同步变化，使核的积分计数一致。该数为本例程序版本的换算常数。若修改每轨道强度或其它缩放，应重新核对，不能继续沿用单位标签。

前三种任务的 `DOS_curve.txt` 第 1 至 5 列分别为能量、TDOS、OPDOS、A-PDOS、B-PDOS；Hirshfeld 任务则第 3、4 列直接为 A/B-PDOS。`orginfo.txt`、`DOS_line.txt` 保存能级设置和竖线信息；LDOS 使用独立的 `LDOS_curve.txt`、`LDOS_line.txt`。

## 提取与重绘

从仓库根目录调用脚本，替换实际工作目录和输出路径：

```bash
python examples/orca/minimal/orbital-dos-cda/analyze.py \
  --work-root /path/to/work --output-dir /path/to/output
python examples/orca/minimal/orbital-dos-cda/plot.py \
  --data /path/to/output/orbital-data.npz \
  --output /path/to/output/orbital-dos.png \
  --cda-output /path/to/output/cda-water.png
```

[analyze.py](analyze.py)检查本例 48/24/24 的完整空间及归一化，从 AO 系数、重叠矩阵独立重建 Mulliken/SCPA、跨片段重叠、FO 系数及 GCDA/ECDA。它还按相同能级和核重建曲线，区分有限能窗计数与完整态数。LDOS 权重由原生轨道空间求值得到，脚本核对其展宽，并传播原生导出有效数字的舍入误差。

[orbital-analysis.json](orbital-analysis.json)保存模型、分区、统计与单位，[orbital-data.npz](orbital-data.npz)保存完整 48 条轨道的成分、FO 矩阵、能级、逐轨道 CDA 和绘图曲线。[plot.py](plot.py)从这些数据重绘，图中 Ha→eV 的横、纵轴同时转换，FO 图按窗口和 `20%` 连线阈值展示，完整小项仍保存在数据中。

脚本限定当前实数闭壳层模型和原子顺序，不用于自动处理开壳层、自然轨道、复杂 ghost 或周期轨道。换体系时，先核对轨道空间、参考片段和软件支持，再调整提取逻辑。
