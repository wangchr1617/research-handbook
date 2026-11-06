# VASP 隐式溶剂计算

**适用环境：Linux + PBS（安装 VASPsol 的 VASP）。**

隐式溶剂用连续介质描述溶剂环境，适合先估计溶剂极化对能量的影响；需要具体氢键、配位或溶剂重排时，还应考虑显式溶剂。

## 同构型真空与溶剂对照

[最小案例](../../../examples/vasp/minimal/implicit-solvation)在 10 Å 立方盒中放置一个水分子，用同一 VASPsol 程序做两次单点计算。两者的结构、赝势、截断能和 k 点完全相同，仅切换溶剂设置。

准备按 O、H 顺序拼接的授权 `POTCAR`，安装 [Python 依赖](../../../examples/vasp/minimal/implicit-solvation/requirements.txt)，指定课题组安装的 VASPsol 程序后提交 [job.pbs](../../../examples/vasp/minimal/implicit-solvation/job.pbs)：

```bash
qsub job.pbs
```

输入包括 [POSCAR](../../../examples/vasp/minimal/implicit-solvation/POSCAR)、[KPOINTS](../../../examples/vasp/minimal/implicit-solvation/KPOINTS)、[真空参数](../../../examples/vasp/minimal/implicit-solvation/INCAR.vacuum)和[溶剂参数](../../../examples/vasp/minimal/implicit-solvation/INCAR.solvent)。溶剂侧的关键设置为：

```text
LSOL = .TRUE.
EB_K = 78.4
```

`EB_K` 是介质相对介电常数；空腔与表面项使用该 VASPsol 实现的默认参数。网格精度影响空腔表面项，应对截断能和盒子尺寸分别检查。

[run.py](../../../examples/vasp/minimal/implicit-solvation/run.py)分别建立 `vacuum/`、`solvent/`，完成计算后调用[后处理](../../../examples/vasp/minimal/implicit-solvation/postprocess.py)。后者检查电子收敛、构型和输入一致性，并确认 `OUTCAR` 实际输出了非零 `Ediel_sol` 溶剂项，结果写入 `solvation-results.json`。

本例真空与溶剂侧总能分别为 −14.21166、−14.52149 eV，差值约 −0.30982 eV；最终 `Ediel_sol` 约为 −1.48299 eV。

总能差取 `E(solvent) − E(vacuum)`。它是本例固定构型和所选连续介质模型下的能量差，不能直接当作包含构象、振动及标准态修正的实验溶剂化自由能；`Ediel_sol` 也不等于完整总能差。

参考：[VASPsol 使用说明](https://github.com/henniggroup/VASPsol/blob/master/docs/USAGE.md)。
