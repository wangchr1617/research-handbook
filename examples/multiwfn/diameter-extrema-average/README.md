# 内切球、势场极小点与 amIGM 平均

**适用环境：Windows、macOS、Linux；已有 Multiwfn、Python、numpy、scipy、scikit-image 和 matplotlib。以下批处理命令使用 Bash。**

本例分别回答局部孔径、势场极小点和空间平均的定义问题。模型包括理想碳位点笼、平面环、周期单 Ar、六 Ar 位点和三个人工水二聚体构型。它们用于核对几何和数值运算；人工构型没有时间间隔，不用于推断真实动力学或吸附自由能。

## 输入与运行目录

- [cage.xyz](cage.xyz)：外接半径 `2.2 Å` 的理想 C₂₀ 位点笼，复用[密度孔洞案例](../cavity-and-potential/README.md)的自建坐标。
- [ring.xyz](ring.xyz)：半径 `3 Å`、位于 `XY` 平面的 12 个 C 位点。
- [periodic-argon.cif](periodic-argon.cif)：边长 `8 Å`、中心一个 Ar 的立方晶胞。
- [octahedral-argon.xyz](octahedral-argon.xyz)：位于三个轴 `±4 Å` 的六个 Ar。
- [esp-seeds.txt](esp-seeds.txt)、[uff-seeds.txt](uff-seeds.txt)：分别含四个、两个确定性的初猜坐标，单位为 **Bohr**。
- [snapshots.xyz](snapshots.xyz)：三帧构造水二聚体；[snapshot-1.xyz](snapshot-1.xyz)、[snapshot-2.xyz](snapshot-2.xyz)、[snapshot-3.xyz](snapshot-3.xyz)为逐帧版本。

将本目录的结构、初猜文件和全部 `.in` 菜单复制到独立工作目录。命令在该工作目录执行，`multiwfn` 已可直接调用。菜单对应 Multiwfn 2026.7.15，使用其默认 C 探针，不要求修改 `settings.ini`。不同版本应核对屏幕选项。

## 内切球的解析对照

```bash
mkdir -p diameter-cage diameter-ring diameter-ring-above diameter-periodic
cp cage.xyz diameter-cage/structure.xyz
cp ring.xyz diameter-ring/structure.xyz
cp ring.xyz diameter-ring-above/structure.xyz
cp periodic-argon.cif diameter-periodic/structure.cif
(cd diameter-cage && multiwfn structure.xyz < ../diameter-cage.in > multiwfn.out)
(cd diameter-ring && multiwfn structure.xyz < ../diameter-ring.in > multiwfn.out)
(cd diameter-ring-above && multiwfn structure.xyz < ../diameter-ring-above.in > multiwfn.out)
(cd diameter-periodic && multiwfn structure.cif < ../diameter-periodic.in > multiwfn.out)
```

[diameter-cage.in](diameter-cage.in)固定几何中心；[diameter-ring.in](diameter-ring.in)只允许在 `XY` 内调整；[diameter-ring-above.in](diameter-ring-above.in)固定在环上方 `2 Å`；[diameter-periodic.in](diameter-periodic.in)固定分数坐标原点。它们分别得到直径 `1.000000`、`2.600000`、`3.811103`、`10.096406 Å`。

第三项说明移出平面后计算的是环外球，第四项说明周期球可以跨越单胞。几何表达式及与贯通孔径的区别见[内切球笔记](../../../notes/计算化学/孔径、内切球与贯通限制.md)。

## ESP 与 UFF 极小点

ESP 使用[弱相互作用案例](../../orca/minimal/weak-interactions/README.md)中同一固定水二聚体的 PBE0/def2-SVP 波函数。按其说明准备 `orca.molden.input`，将文件复制到当前工作目录；已有该文件时可以直接复用，不需为本例重新优化几何。

```bash
mkdir -p esp uff-minima
cp orca.molden.input esp/
cp esp-seeds.txt esp/seeds.txt
cp octahedral-argon.xyz uff-minima/structure.xyz
cp uff-seeds.txt uff-minima/seeds.txt
(cd esp && multiwfn orca.molden.input < ../esp.in > multiwfn.out)
(cd uff-minima && multiwfn structure.xyz < ../uff-minima.in > multiwfn.out)
```

[esp.in](esp.in)、[uff-minima.in](uff-minima.in)设置所搜函数、从 `seeds.txt` 读取初猜，导出 `CPs.txt` 和 `CPprop.txt`。四个水二聚体初猜收敛到四个 `(3,+3)` 点；六 Ar 的两个初猜收敛到同一个中心附近极小点。CP 数量仅针对本初猜集合，不作为全空间覆盖证明。

检查 `CPprop.txt` 的函数值、梯度、Hessian 和特征值。UFF 中心势约为 `−0.8050603 kcal/mol`，三条主曲率约为 `0.1830911 kcal/mol/Bohr²`，可用独立 UFF 求导核对。ESP 的数值 Hessian 还记录与 Poisson 关系的残差。

## 同一入口的平均与单帧场

```bash
mkdir -p average am-frame-1 am-frame-2 am-frame-3
cp snapshots.xyz average/
(cd average && multiwfn snapshots.xyz < ../average.in > multiwfn.out)
for i in 1 2 3; do
  cp "snapshot-$i.xyz" "am-frame-$i/snapshot.xyz"
  (cd "am-frame-$i" && multiwfn snapshot.xyz < ../am-frame.in > multiwfn.out)
done
```

[average.in](average.in)和 [am-frame.in](am-frame.in)采用相同 `20 → -12` 入口：片段为 `1-3` 与 `4-6`，网格原点约为 `(0.8,−1.0,−0.8) Å`，输入坐标为 Bohr，步距为 `0.2 Bohr`，形状为 `17×20×16`。两套菜单都导出 `avgdg_inter.cub`、`avgsl2r.cub`；在单帧目录中，前者就是相应瞬时场。

第一个水始终固定，第二个水只沿 `Y` 平移。共同局部网格在此模型中未被几何预筛，允许直接逐点比较。网格没有覆盖整个体系，不能把它当作完整作用区域积分。

## 提取、解释与重绘

从仓库根目录调用脚本，替换为实际工作目录和输出位置。Python 库沿用[共用读取与绘图依赖](../../orca/minimal/weak-interactions/requirements.txt)；脚本复用仓库中的正交单标量 [Cube 读取器](../../orca/minimal/weak-interactions/analyze.py)。

```bash
python examples/multiwfn/diameter-extrema-average/analyze.py \
  --work-root /path/to/work --output-dir /path/to/output
python examples/multiwfn/diameter-extrema-average/plot.py \
  --data /path/to/output/average-data.npz \
  --output /path/to/output/amigm-average.png
```

[analyze.py](analyze.py)默认读取 `multiwfn.out`，可用 `--log-name` 改日志名。它核对四个几何半径、CP 属性和 UFF 解析导数，再检查平均场与同入口单帧场的网格、参考片段及数值。此脚本限定本例模型与菜单，不是任意轨迹的通用解析器。

输出包括：

| 文件 | 内容 |
| --- | --- |
| [diameter-extrema.json](diameter-extrema.json) | 四个内切球、四个 ESP 极小点、一个 UFF 极小点及单位 |
| [average-analysis.json](average-analysis.json) | 平均的定义、网格、统计量和原始网格摘要 |
| [average-data.npz](average-data.npz) | 平均场、平均几何单帧场、总体标准差、TFI、着色场和坐标 |
| [plot.py](plot.py) | 从 NPZ 重绘局部截面 |

同入口瞬时场均值与原生平均场的差异不超过约 `6.7×10⁻⁸ e/Bohr⁴`，标准差由逐帧场以 `ddof=0` 计算。平均几何场和平均场有明显差别；着色场也不等于每帧带符号密度的算术平均。真实轨迹的统计分析还需平衡采样和相关时间检查。

NPZ 的 `mean` 保存原生平均 Cube，`std` 和 `tfi` 则由逐帧导出值计算，TFI 的分母是这些值的算术平均。两种平均在导出精度内接近，但不能要求保存的 `std/mean` 与 `tfi` 逐位相等。TFI 是相对涨落指标；交换帧顺序不会改变它，因此它本身不给出接触寿命、相关时间或转移速率。
