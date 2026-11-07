# 周期水二聚体的响应与局部场

**适用环境：已有 CP2K、Multiwfn 和 [Python 依赖](requirements.txt)的 Windows、macOS、Linux；命令使用 Bash。**

用一个自建固定水二聚体演示周期波函数的元数据检查、NCI/IGMH 局部网格、TDA 跃迁系数与 NTO。模型沿用[周期 CDA 案例](../periodic-cda/README.md)的几何和基态条件；这里不优化结构。方法说明见[周期 NCI/IGMH](../../../../notes/CP2K/电子结构与响应/CP2K周期NCI与IGMH的边界和网格.md)与[周期激发/NTO](../../../../notes/CP2K/电子结构与响应/CP2K周期激发、跃迁系数与NTO.md)。

## 基态、响应和轨道导出

将本目录文件复制到独立工作目录，保持下面的目录层次。CP2K 应能找到 `BASIS_MOLOPT` 和 `GTH_POTENTIALS`；`cp2k.psmp`、`multiwfn` 替换为实际可用的程序入口。

```bash
mkdir -p periodic-tddfpt
cp cp2k.inp structure.xyz periodic-tddfpt/
(cd periodic-tddfpt && OMP_NUM_THREADS=2 cp2k.psmp -i cp2k.inp -o cp2k.out)
python prepare.py periodic-tddfpt/optical-MOS-1_0.molden .
```

[cp2k.inp](cp2k.inp)使用 `8×8×8 Å³` 晶胞、Γ 点、PBE/DZVP-MOLOPT-SR-GTH、O `q6`/H `q1`、`CUTOFF 400 Ry`、`REL_CUTOFF 50 Ry`、`EPS_DEFAULT 10⁻¹²` 和 `EPS_SCF 10⁻⁸`。SCF 对角化并求出全部轨道，Molden 导出 46 个轨道与 12 位系数、晶胞及赝势元数据；闭壳层有 16 个显式电子。

响应采用 `KERNEL FULL` 的 TDA、三个单重态、`CONVERGENCE 10⁻⁷ Ha`、`MIN_AMPLITUDE 10⁻⁶`。先检查 SCF/TDDFPT 均收敛及程序正常结束。当前模型的计算分别经过 22 次 SCF 和 5 次 Davidson 迭代。

[prepare.py](prepare.py)核对六个原子的 `[Pseudo]`，在分析副本的 `[GTO]` 前插入 O 6/H 1 的 `[Nval]`，并准备各任务目录。这个兼容处理面向 Multiwfn 2026.7.15 的本机构建：原文件虽带 `[Pseudo]`，其读取器对 CP2K 文件仍显示错误的 `+4`；补充后应为 0。原始 Molden 保持不变，其他模型不能原样套用元素映射。

## 原生后处理

```bash
for tag in grid translated igmh igmh-translated grid-fine igmh-fine nto; do
  (cd "$tag" && multiwfn periodic.molden -silent < input.txt > multiwfn.out)
done
```

菜单按 Multiwfn 2026.7.15 编写。[grid.in](grid.in)计算 NCI，导出 `func1.cub` 为着色量、`func2.cub` 为 RDG；[igmh.in](igmh.in)采用片段 `1–3` / `4–6`，导出 `dg_inter.cub`、`sl2r.cub` 等。[nto.in](nto.in)选第一态并保存 `nto.mwfn`。所有目录应从同一份匹配的波函数开始。

粗网格原点为 `(2,2,4) Bohr`，步长 `0.3 Bohr`，点数 `23×13×13`；平移目录仅将 x 原点增加一个晶胞 `15.117808997 Bohr`。细网格保持相同覆盖端点，步长 `0.2 Bohr`、点数 `34×19×19`。这两种设置用于接口及空间采样演示，定量分析还需继续收敛测试。

载入时确认 O 的有效核电荷、总电荷 0、16 个显式电子和 `8 Å` 三维晶胞。当前程序自动加载两个 O 各 2 个芯电子的 EDF；网格是该处理下的密度场，不要把它标成未经补芯的纯价电子密度。保留原生 RDG 高密度筛选和 IGMH 设置，以日志为准；图中的 `RDG < 0.5` 是绘图掩膜。

小晶胞会产生扩大周期图像求和范围的提示。晶胞平移一致性只验证对应点的场值，不能代替图像范围收敛；需定量比较时，再逐项测试对应会话/工作配置并记录实际值。

## 独立重建和作图

下面命令从仓库根目录执行，`/path/to/work` 指前述工作目录。脚本复用仓库的 [Cube 读取器](../../../orca/minimal/weak-interactions/analyze.py)，因此需要相应依赖及完整仓库相对结构。

```bash
python examples/cp2k/minimal/periodic-response/analyze.py \
  --work-root /path/to/work --output-dir /path/to/work/derived
```

[analyze.py](analyze.py)检查导出轨道数量、占据、跃迁索引与范数，直接对 CP2K 幅度矩阵作 SVD，并对照第一态的原生 NTO 导出。三个态的打印幅度平方和均在 `1±10⁻⁶` 附近；独立 SVD 与原生第一态权重最大差约 `2.9×10⁻¹⁰`。它还比较粗网格与平移网格的坐标和四种场值，当前 Cube 精度下最大场值差为 0。

派生数据见 [response.json](response.json)和 [response.npz](response.npz)。JSON 保存模型、版本、输入/几何/原始波函数/分析副本的哈希、激发能、强度、NTO 权重和核对量；NPZ 保存三个跃迁矩阵、细网格场、坐标、能量域展宽谱。图见[场切片](../../../../notes/CP2K/assets/periodic-fields.png)与[激发谱/NTO](../../../../notes/CP2K/assets/periodic-excitations.png)。

三根能量约为 `9.35049`、`10.33149`、`11.00357 eV`；谱线用标准差 `0.15 eV` 的面积归一化高斯展宽。输出演示人工周期盒中固定结构的响应；紧凑基组、有限根数和当前采样不能代表液态水或真实材料的定量吸收谱。NTO 文件的能量字段保存权重，不能作为基态轨道能量使用。
