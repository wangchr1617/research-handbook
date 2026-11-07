# 坐标变换、跨边界分子与几何自由体积

**适用环境：Windows、macOS、Linux；已有 Multiwfn 和 Python 绘图依赖。**

本例只进行结构与几何网格分析。三个自建模型分别是固定水二聚体、边长 4 Å 的单水 P1 晶格和边长 8 Å 的单 Ar P1 晶格；后两个用于检查周期几何，不作为真实平衡晶相。波函数的 [ODI 例子](../../orca/minimal/weak-interactions/README.md#hirshfeld-轨道成分与-odi)另复用已有 ORCA 水二聚体计算。

## 准备与运行

将 [structure.xyz](structure.xyz)、[water-lattice.cif](water-lattice.cif)、[argon.cif](argon.cif)和六份菜单复制到独立工作目录。菜单按 Multiwfn 2026.7.15 编写，运行前核对当前版本的实际提示。在该工作目录执行：

```bash
mkdir -p rotate cluster free-050 free-025 free-scale free-cap
cp structure.xyz rotate/
cp water-lattice.cif cluster/

(cd rotate && multiwfn structure.xyz < ../rotate.in > multiwfn.out)
(cd cluster && multiwfn water-lattice.cif < ../cluster.in > multiwfn.out)

for name in free-050 free-025 free-scale free-cap; do
  cp argon.cif "$name/"
  (cd "$name" && multiwfn argon.cif < "../$name.in" > multiwfn.out)
done
```

| 菜单 | 操作与输出 |
| --- | --- |
| [rotate.in](rotate.in) | 对整个二聚体绕 Y 轴旋转 90°，再将第一水的几何中心移到原点，导出 `rotated.xyz` |
| [cluster.in](cluster.in) | 拼接跨边界水为 `whole.xyz`；按接触倍数 1.2 提取中心及邻近完整分子，导出 `cluster.xyz` |
| [free-050.in](free-050.in) | 周期自由区域，请求间距 0.50 Å，展示边界不封口 |
| [free-025.in](free-025.in) | 请求间距 0.25 Å，其余同上 |
| [free-scale.in](free-scale.in) | 细网格，原始半径球放大至 1.2 倍，平滑方法保持默认 |
| [free-cap.in](free-cap.in) | 细网格，原始半径不变，保留默认展示边界封口 |

四个自由区域目录各自产生 `free_prim.cub` 和 `free_smooth.cub`。前者是二值占据补集，后者是显示场；二者不能互相替代。原始网格保留在计算工作目录。

## 独立提取与重绘

Python 使用现有 [numpy、matplotlib 等依赖](../../orca/minimal/weak-interactions/requirements.txt)。提取脚本从仓库相对路径复用已有 [Cube 读取器](../../orca/minimal/weak-interactions/analyze.py)，请在保留仓库结构的前提下调用。在仓库根目录运行，替换工作目录的绝对路径：

```bash
python examples/multiwfn/geometry-voids/analyze_geometry_voids.py \
  --work-root /path/to/work --output-dir /path/to/work
python examples/multiwfn/geometry-voids/plot_geometry_voids.py \
  --data /path/to/work/geometry-voids.json \
  --output /path/to/work/geometry-voids.png
```

[analyze_geometry_voids.py](analyze_geometry_voids.py)核对整体旋转矩阵、中心位置、水分子内部几何和整数晶格平移；按同一周期半径球独立重建原始二值网格，使用实际步矢积分并与日志比较。它限定本例的正交晶胞、单 Ar 半径 1.88 Å 及水的原子顺序，不是任意晶体孔隙分析器。

[geometry-voids.json](geometry-voids.json)保留小型科学数据、坐标、实际网格与截面、源 Cube 摘要和几何参照。已有此文件时，可单独运行 [plot_geometry_voids.py](plot_geometry_voids.py)重绘，无需重新运行 Multiwfn。

## 结果怎样判断

- 刚体旋转前后原子间距离不变，第一水的几何中心为原点。这里操作的是结构文件，不将未旋转的轨道系数用于新方向的电子结构分析。
- 跨边界水拼接后为 3 个原子，两条 O–H 分别约为 0.9572、0.9578 Å；邻近团簇为 5 个完整水、15 个原子，各分子的内部几何相同。
- 单 Ar 模型的解析几何自由体积为 484.16686 Å³。请求 0.50、0.25 Å 网格分别得到约 487.72750、483.81354 Å³；实际间距约 0.5333、0.2581 Å，应从 Cube 读取。
- 原始半径放大 1.2 倍后，自由体积约 463.87735 Å³，但本版默认平滑场与未放大时相同。
- 边界封口前后屏幕体积相同，导出二值网格却被改写。脚本按封口前定义重建统计；不能把展示封口当作孔道真实闭合。

图中的平滑截面取实际网格层，`z≈4.129 Å`；它没有插值成精确的球心平面。完整解释见[坐标与团簇](../../../notes/计算化学/坐标变换、周期拼接与分子团簇.md)和[自由空间与探针](../../../notes/计算化学/晶体自由空间、平滑网格与探针体积.md)。
