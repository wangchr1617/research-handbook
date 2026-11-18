# VASP 批量计算

**适用环境：Linux（PBS 计算）；Windows / macOS / Linux（输入准备与结果分析）。**

把硅原胞中的一个原子沿笛卡尔 x 移动 0.03 Å，先问同一套 VASP 设置给出的能量、力和位力怎样变化。仓库的两构型案例把参考态和位移态分别运行，适合用来确认构型与输出一一对应，再扩大到更多结构。

## 一、让两个硅构型共用电子设置

[配套案例](../../../examples/vasp/minimal/batch-single-points)计算硅原胞及一个小位移构型，两组采用相同截断能、k 网格和电子精度。

| 文件 | 用途 |
| --- | --- |
| [POSCAR](../../../examples/vasp/minimal/batch-single-points/POSCAR)、[POSCAR.distorted](../../../examples/vasp/minimal/batch-single-points/POSCAR.distorted) | 两个待标注构型 |
| [INCAR](../../../examples/vasp/minimal/batch-single-points/INCAR) | `ENCUT=450 eV`、`ISIF=2` 的单点设置 |
| [KPOINTS](../../../examples/vasp/minimal/batch-single-points/KPOINTS) | Γ 中心 `7 × 7 × 7` 网格 |
| [run.py](../../../examples/vasp/minimal/batch-single-points/run.py)、[job.pbs](../../../examples/vasp/minimal/batch-single-points/job.pbs) | 顺序计算与 PBS 入口 |
| [postprocess.py](../../../examples/vasp/minimal/batch-single-points/postprocess.py) | 检查计算、调用通用导出器并核对标签 |

准备授权 Si 势，加载 VASP 与案例 Python 依赖，在案例目录运行：

```bash
qsub job.pbs
```

作业建立 `runs/reference`、`runs/distorted` 两个独立目录，已有同名目录时停止。两个结构文件使用分数坐标，所以第一颗 Si 的三个分数分量都变了。乘回原胞的三个向量后，实际只沿笛卡尔 x 移动。

## 二、验收两个单点，再写出标签

已有输出时，在案例目录运行 `python3 postprocess.py`。脚本先逐项验收电子收敛，再用[通用导出器](../../../scripts/structure/vasp_to_xyz.py)收集末帧，以 `e_fr_energy` 作为本例能量标签。写入临时 ExtXYZ 后，回读晶胞、坐标、周期性、能量、力和位力，与原始 `vasprun.xml` 交叉核对。通过后才发布 `labeled-structures.xyz` 与 `batch-results.json`。

## 三、扩大批量时保留失败状态

已有一组 POSCAR 时，可使用[prepare_jobs.py](../../../scripts/vasp/prepare_jobs.py)建立目录；已有模板时，也可扫描截断能或晶格线性缩放。先查看 `--help`，注意缩放命令的参数是长度比，不是体积比。更完整的单变量操作见[参数收敛测试](VASP参数收敛测试.md)。

用 VASPKIT 生成多组输入前，先核对一个代表性结构和所选功能。不同成分应分别生成正确的 POTCAR，不能把同一套势直接复制给所有目录。

作业较多时，可按集群支持的方式分批或使用 PBS 数组。目录里已有 OUTCAR 时，应先区分完成、未收敛或中断状态，不以“文件存在”代替完成检查。[summarize_outputs.py](../../../scripts/vasp/summarize_outputs.py)可帮助汇总能量、受力和收敛情况；原始输出仍是最终核对依据。

## 四、从标签交接到训练数据

标签导出、位力单位及数据划分见[训练数据准备](../动力学与机器学习/VASP训练数据准备.md)。需要在线学习与力场加速时，参见[机器学习力场](../动力学与机器学习/VASP机器学习力场.md)，不要将其混合预测轨迹直接当作纯 DFT 标注。
