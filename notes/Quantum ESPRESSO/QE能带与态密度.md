# Quantum ESPRESSO 能带与态密度

从同一份收敛的 `pw.x` 基态密度分出两条路线。路径上的本征值用于画能带，均匀网格上的本征值用于积分 DOS。用独立目录或复制完整的自洽工作数据保存两路输出。

| 阶段 | 输入要点 | 输出与核对 |
| --- | --- | --- |
| SCF | `calculation='scf'`，收敛结构、赝势、截断和规则 k 网格 | 确认 `prefix/outdir` 下有该体系的自洽数据 |
| 能带 | `calculation='bands'`，使用当前晶胞的 `K_POINTS crystal_b` 路径并准备足够空带 | `bands.x` 以匹配的 `prefix/outdir` 读结果，用 `filband` 指定输出 |
| DOS | `calculation='nscf'`，用更密的规则网格，按积分方法设置占据和采样 | `dos.x` 写出总 DOS。按需用 `projwfc.x` 分解原子、轨道和自旋 |

## Si 原胞练习

用 [QE 基础](QE基础知识.md)的 Si 原胞输入做 `scf.in`，将 Si 势文件名改为实际值。执行 `pw.x -in scf.in > scf.out`，确认电子收敛后，把 `tmp`、`pseudo` 和输入复制到两个独立工作目录。后续命令分别在对应分支执行，均使用 `prefix='si'` 和 `outdir='./tmp'`。

能带分支把 `calculation` 改为 `'bands'`，在 `&SYSTEM` 中加 `nbnd=8`，将 k 点卡替换为下列短路径。该原胞的 `(0.5, 0, 0.5)` 对应一个 X 点。

```text
K_POINTS crystal_b
2
0.0 0.0 0.0 20
0.5 0.0 0.5 1
```

保存为 `bands.in` 并运行 `pw.x -in bands.in > bands.out`。将下段保存为 `bands_pp.in`，执行 `bands.x -in bands_pp.in > bands_pp.out`。

```text
&BANDS
 prefix='si', outdir='./tmp', filband='si.bands'
/
```

DOS 分支从 `scf.in` 改成 `calculation='nscf'`、`occupations='tetrahedra'`、`nbnd=8` 和 `K_POINTS automatic` 下的 `8 8 8 0 0 0`。保存为 `nscf.in` 并运行 `pw.x -in nscf.in > nscf.out`。将下段保存为 `dos.in`，执行 `dos.x -in dos.in > dos.out`。

```text
&DOS
 prefix='si', outdir='./tmp', fildos='si.dos', DeltaE=0.05
/
```

## 看结果

QE 7.6 下用 Si 的 PBE 模守恒赝势 `Si_ONCV_PBE-1.1.upf`试跑，`si.bands` 头部给出 8 条带和 21 个 k 点，`si.dos` 给出能量（eV）、总 DOS 和积分 DOS。Si 可用价带顶置零，并用更完整的路径与加密的均匀网格核对间接带边。Al 等金属则对齐费米能级，扫描网格与展宽。比较 DOS 时统一每胞或每原子、自旋和能量单位。

语法见 [pw.x](https://www.quantum-espresso.org/Doc/INPUT_PW.html)、[bands.x](https://www.quantum-espresso.org/Doc/INPUT_BANDS.html)与 [dos.x](https://www.quantum-espresso.org/Doc/INPUT_DOS.html)。
