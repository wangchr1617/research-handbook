# 水二聚体的空穴、NTO 与 IFCT

**适用环境：已有 Multiwfn 及 [Python 依赖](requirements.txt)的 Windows、macOS、Linux；命令使用 Bash。**

本例对同一份 CP2K 周期 TDA 响应比较网格积分、NTO 和两种片段分区，并用独立矩阵计算复现原生后处理的截断。输入约定与主要方法见 [CP2K 周期激发](../../../notes/CP2K/电子结构与响应/CP2K周期激发、跃迁系数与NTO.md)。

## 准备同源文件

先按[周期响应案例](../../cp2k/minimal/periodic-response/README.md)生成 CP2K 输出和已检查有效核电荷的 `periodic.molden`。模型是自建固定水二聚体、`8 Å` 立方周期盒、Γ 点、PBE/DZVP-MOLOPT-SR-GTH、O `q6`/H `q1`，46 个空间轨道、16 个显式电子。它演示数据接口与后处理，不代表液态水或收敛的材料吸收谱。

从仓库根目录调用 [prepare.py](prepare.py)，替换两个输入文件及新的工作目录：

```bash
python examples/multiwfn/excitation-analysis/prepare.py \
  --wavefunction /path/to/periodic-response/grid/periodic.molden \
  --response /path/to/periodic-response/periodic-tddfpt/cp2k.out \
  --output-dir /path/to/excitation-work
```

脚本检查 O 6/H 1 的 `[Nval]`、`8 Å` 晶胞和占据数，为 11 项分析生成独立目录和 `input.txt`。已有工作目录会被拒绝，以免覆盖。响应路径写入交互输入，计算期间保留该原始输出文件；每项分析都复制相同的波函数。

## 运行原生分析

```bash
work=/path/to/excitation-work
for tag in hole-32 hole-48 hole-64 cross-32 orbitals-32 matrices \
           nto-1 nto-2 nto-3 ifct-mulliken ifct-hirshfeld; do
  (cd "$work/$tag" && multiwfn periodic.molden -silent < input.txt > multiwfn.out)
done
```

菜单按 Multiwfn 2026.7.15 编写，具体任务如下：

| 目录 | 输出与用途 |
| --- | --- |
| `hole-32`、`hole-48`、`hole-64` | 第三态的完整空穴/电子、Sm、Sr、跃迁密度和 CDD；三个单胞网格比较 |
| `cross-32` | 同一粗网格的交叉项，单独保存，避免覆盖总分布 |
| `orbitals-32` | 46 个 MO 的标量 Cube，用于独立重建密度 |
| `matrices` | 包含真实周期重叠矩阵的 `matrices.mwfn` |
| `nto-1` 至 `nto-3` | 每态独立的 `nto.mwfn` 与权重 |
| `ifct-mulliken`、`ifct-hirshfeld` | 第三态两水片段的转移量，及原子矩阵 `atmCTmat.txt` |

网格覆盖一个晶胞，原点 0。周期选项 `4` 输入的是 Bohr 步长；生成器使用约 `0.472432`、`0.314954`、`0.236216 Bohr`，得到 `32³`、`48³`、`64³` 个点，周期终点不重复采样。核对实际步进矢量、点数及有限性，不能只看程序退出码。

当前默认图像范围保留，小晶胞提示仍应作为后续定量工作的收敛检查项。周期轨道本身不含被消去的芯电子；前置案例的有效核电荷映射触发了近似 EDF 补芯，但空穴/电子来自相应轨道的跃迁，不是把芯密度当成激发电子加进去。

## 重建与检查

```bash
python examples/multiwfn/excitation-analysis/analyze.py \
  --work-root /path/to/excitation-work \
  --response /path/to/periodic-response/periodic-tddfpt/cp2k.out \
  --output-dir /path/to/excitation-work/derived
```

[analyze.py](analyze.py)复用[响应系数/Cube 读取器](../../cp2k/minimal/periodic-response/analyze.py)和[MWFN/分块矩阵读取器](../../orca/minimal/orbital-dos-cda/analyze.py)，需保持仓库相对目录结构。它会：

- 独立积分三种网格，核对 Sm、Sr 和 `CDD = electron − hole`；CDD 的近零抵消按 Cube 六位有效数字传播舍入界。
- 用导出的 46 个 MO 和完整幅度矩阵重建密度，并单独模拟原生网格交叉项的 `0.01` 内部幅度阈值。原生阈值下重建与总场最大差小于 `6.6×10⁻⁷ a.u.`，与交叉项最大差小于 `4.1×10⁻⁸ a.u.`；完整矩阵与阈值版本的差异另外保存。
- 将三个态的原生 NTO 权重与独立 SVD 比较，最大差小于 `4.4×10⁻¹⁰`。
- 用周期 S、AO 系数与幅度重建原生 Mulliken-like 的 `0.001` 内部幅度乘积筛选和归一化，原子 IFCT 矩阵最大差小于 `4.9×10⁻⁹`；再按两水片段求和，核对行列方向、边际和电子收支。

保存的三态响应幅度受原输出打印精度限制，平方和与 1 的偏差小于 `9×10⁻⁷`。比较 NTO 权重、网格积分及 IFCT 时，分别保留幅度舍入、空间采样和分区截断的误差来源，不通过统一归一化掩盖差异。

三个网格的空穴积分约为 `0.984670`、`0.999194`、`0.999982`，Sr 约为 `0.407730`、`0.424657`、`0.430312`。归一化逐渐改善时 Sr 仍在变化；本例没有把最细网格视为所有描述符已收敛。

原生 Mulliken-like、Hirshfeld 给出的 A 片段净增电子分别约为 `0.125046`、`0.083235`。同一 Mulliken 定义下若保留完整幅度乘积，独立重建为约 `0.125663`，展示了分区差异和内部截断的不同来源。

派生数据见 [analysis.json](analysis.json)和 [analysis.npz](analysis.npz)。JSON 保存模型、版本、源文件哈希、网格对照、原生重建误差与片段数据；NPZ 保存三态幅度矩阵、绘图切片及 IFCT 矩阵。完整原始 Cube 留在计算目录，避免发布大量重复网格。

图见[空穴/电子切片](../../../notes/计算化学/assets/hole-electron-fields.png)与[IFCT 矩阵](../../../notes/计算化学/assets/ifct-matrices.png)。前者选 `z=3.5 Å`，原子为 xy 投影；空穴/电子共用色标，差值用对称色标。周期质心和宽度依赖所选晶胞，本例的静态图和矩阵不直接解释为真实传输轨迹、寿命或激子结合能。
