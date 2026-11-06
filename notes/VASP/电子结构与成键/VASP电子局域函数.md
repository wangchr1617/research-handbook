# VASP 电子局域函数 ELF

**适用环境：Windows、macOS、Linux（Multiwfn 与绘图）；Linux + PBS（VASP）。**

贡献者：胡京京、王昌锐

ELF 是描述电子局域性的无量纲函数，通常介于 0 和 1。较高值可帮助识别共价键、孤对电子等局域区域，0.5 是均匀电子气的参考值；低 ELF 不能简单解释成“电子完全离域”，也不能直接当作电荷或键能。

## 输入与提交

以硅原胞为例，案例提供 [POSCAR](../../../examples/vasp/minimal/electron-localization/POSCAR)、[INCAR](../../../examples/vasp/minimal/electron-localization/INCAR)、[KPOINTS](../../../examples/vasp/minimal/electron-localization/KPOINTS)、[POTCAR.spec](../../../examples/vasp/minimal/electron-localization/POTCAR.spec)、[job.pbs](../../../examples/vasp/minimal/electron-localization/job.pbs) 和 [postprocess.py](../../../examples/vasp/minimal/electron-localization/postprocess.py)。

准备授权 Si 势，加载 VASP、MPI、Multiwfn 和 Python [绘图依赖](../../../examples/vasp/minimal/electron-localization/requirements.txt)，执行 `qsub job.pbs`。

本例在静态计算中加入：

```text
LELF = .TRUE.
NPAR = 1
PREC = Accurate
LREAL = .FALSE.
```

`LELF` 输出 `ELFCAR`，`NPAR=1` 按 [LELF 手册](https://vasp.at/wiki/LELF)设置。例子采用非自旋极化方案；非共线等扩展计算的支持范围需另查相应版本。

## 用 Multiwfn 导出网格

后处理先检查 VASP，再由 [analyze.py](../../../examples/vasp/minimal/electron-localization/analyze.py) 载入 `ELFCAR`，按 [multiwfn.in](../../../examples/vasp/minimal/electron-localization/multiwfn.in) 的操作选择 `13 → 0`，导出 `elf.cub`。

`ELFCAR` 与 `CHGCAR` 的文件布局相似，但其中的 ELF **没有电荷密度单位**，不能按电子密度除以晶胞体积或对其积分求电荷，见 [ELFCAR 手册](https://vasp.at/wiki/ELFCAR)。脚本同时检查值域，并将网格尺寸和极值写入 `elf-analysis.json`。

## 查看切面

[plot.py](../../../examples/vasp/minimal/electron-localization/plot.py) 在第三分数坐标约为 0.125 的实际网格层取切面，画出由第一、第二晶格向量张成平面内的 ELF。图保留斜晶胞的夹角，未对网格做额外平滑。

![硅原胞电子局域函数切面](../assets/si-elf.png)

本例使用 350 eV 截断能和 3×3×3 k 网格，展示的是一个切面，不是沿该方向的整体投影。修改脚本中的 `FRACTION_C` 可选择其他层；改变网格精度后应重新生成图，不应把粗网格经插值后的平滑外观当作更高精度。

已有 `ELFCAR` 时执行 `python3 analyze.py` 即可重新导出并绘图；已有 `elf.cub` 时执行 `python3 plot.py` 只重画。需要交互查看等值面或任意切面时，也可直接用 VESTA 打开 `ELFCAR`，并根据关注的区域调整等值面或色标。
