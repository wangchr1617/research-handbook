# 周期水二聚体的 CDA

**适用环境：已有 CP2K、Multiwfn 和 numpy 的 Windows、macOS、Linux；命令使用 Bash。**

本例将自建固定水二聚体置于 `8×8×8 Å³` 周期盒子，比较复合物与两个中性单重态水片段。它演示 Γ 点完整轨道空间和周期重叠的处理，不代表表面吸附或液态水。方法与结果解释见[周期 CDA 笔记](../../../../notes/CP2K/电子结构与响应/CP2K与Multiwfn的周期CDA分析.md)。

## 计算输入

[complex.xyz](complex.xyz)、[A.xyz](A.xyz)、[B.xyz](B.xyz)保持同一晶胞中的原子顺序和坐标。三份结构使用同一 [cp2k.inp](cp2k.inp)：PBE、DZVP-MOLOPT-SR-GTH、O `q6`/H `q1`、`CUTOFF 400 Ry`、`REL_CUTOFF 50 Ry`、`EPS_DEFAULT 10⁻¹²`、`EPS_SCF 10⁻⁸`。这些是教学模型参数，其他体系按能量与目标性质检查收敛。

把本目录结构、输入和两份 `.in` 菜单复制到独立工作目录。在该目录执行：

```bash
mkdir -p periodic-complex periodic-A periodic-B periodic-cda
for tag in complex A B; do
  cp "$tag.xyz" "periodic-$tag/structure.xyz"
  cp cp2k.inp "periodic-$tag/"
  (cd "periodic-$tag" && OMP_NUM_THREADS=2 cp2k.psmp -i cp2k.inp -o cp2k.out)
done
```

`BASIS_MOLOPT`、`GTH_POTENTIALS` 需能由已有 CP2K 环境找到，按实际安装设置数据路径。各任务独立工作目录，项目名均为 `periodic`，输出 `periodic-MOS-1_0.molden` 等文件不会互相覆盖。

输入使用对角化、`ADDED_MOS -1` 和 `MO_MOLDEN/NLUMO -1`，导出全部可用轨道；`NDIGITS 12`、`UNIT ANGSTROM`、`WRITE_CELL T`、`WRITE_PSEUDO T` 保留系数和元数据。核对复合物 46 AO/轨道、16 显式电子，片段各 23 AO/轨道、8 电子；同时检查 SCF 收敛。

读取端还应检查总电荷。部分 Multiwfn 构建未自动采用 CP2K 的 `[Pseudo]`，此时在每份分析副本前部加入对应的 O 6/H 1 `[Nval]`，保持原始导出，见[元数据兼容检查](../../../../notes/CP2K/电子结构与响应/CP2K周期NCI与IGMH的边界和网格.md#从-cp2k-输出到正确读入)。该补充影响有效核电荷和补芯密度，不改变已有轨道的周期重叠定义。

## 导出片段矩阵与运行 CDA

```bash
for tag in A B; do
  (cd "periodic-$tag" && multiwfn periodic-MOS-1_0.molden -silent < ../matrices.in > matrices.log)
done
(cd periodic-cda && multiwfn ../periodic-complex/periodic-MOS-1_0.molden -silent < ../cda.in > run.log)
```

[matrices.in](matrices.in)在每个片段目录保存 `matrices.mwfn`，包含完整轨道与周期重叠。[cda.in](cda.in)先运行两片段 CDA，导出 `coFO.txt`、`ovlpint.txt`，再保存复合物的 `complex.mwfn`，用于独立重建。

菜单按 Multiwfn 2026.7.15 编写。若目录中已有同名重叠矩阵，确认其结构/晶胞/AO 顺序再决定是否复用；本例从独立空目录开始，直接计算当前周期重叠。

## 提取与结果检查

从仓库根目录调用 [analyze.py](analyze.py)，替换路径：

```bash
python examples/cp2k/minimal/periodic-cda/analyze.py \
  --work-root /path/to/work --output /path/to/work/periodic-cda.json
```

脚本复用仓库的 [MWFN/分块矩阵读取器](../../../orca/minimal/orbital-dos-cda/analyze.py)，检查 `46=23+23`、电子数、S 正交性、片段重叠块和晶胞，再重建 AO→FO、GCDA 与 ECDA。它同时检查同一 AO 分块下的 Mulliken 电子增量，结果保存在 [periodic-cda.json](periodic-cda.json)。

本模型中 \(d\approx0.000454\)、\(b\approx0.026625\)、\(d-b\approx-0.026171\)、\(r\approx-0.043861\)，ECDA 的 A→B 净项约为 `−0.030887`。B 的 Mulliken 电子数约为 `7.969113`，与 ECDA 在当前完整空间和整数占据条件下对应；不要求其他原子电荷定义给出相同结果。

保留晶胞时，原生重叠下 \(C^\mathrm TSC-I\) 的最大绝对元素约为 `6.5×10⁻⁸`。若只删去复合物 Molden 的晶胞字段而保留周期系数，孤立重叠下同一检查可增至约 `9.5×10⁻²`。这是错误元数据的反例，不是另一种等价后处理设置。
