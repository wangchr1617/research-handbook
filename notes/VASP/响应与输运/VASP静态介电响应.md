# VASP 静态介电响应

**适用环境：Linux（PBS 计算）；Windows / macOS / Linux（输入编辑与结果分析）。**

`LEPSILON` 用密度泛函微扰理论计算固定离子位置的电子介电响应、Born 有效电荷和压电张量。[官方说明](https://vasp.at/wiki/index.php/LEPSILON)中的静态电子介电张量，不应与包含离子振动贡献的低频总介电常数混淆。

## 准备与提交

[最小案例](../../../examples/vasp/minimal/dielectric-response)采用金刚石硅的两原子原胞。可用 VASPKIT 准备静态输入和授权 Si 势，再核对以下文件：

| 文件 | 用途 |
| --- | --- |
| [POSCAR](../../../examples/vasp/minimal/dielectric-response/POSCAR) | 硅原胞结构 |
| [INCAR](../../../examples/vasp/minimal/dielectric-response/INCAR) | `LEPSILON`、精度和响应设置 |
| [KPOINTS](../../../examples/vasp/minimal/dielectric-response/KPOINTS) | Γ 中心 `3 × 3 × 3` 网格 |
| [job.pbs](../../../examples/vasp/minimal/dielectric-response/job.pbs) | PBS 作业入口 |
| [analyze.py](../../../examples/vasp/minimal/dielectric-response/analyze.py) | 提取张量并检查硅的对称性 |

关键设置为：

```text
LEPSILON = .TRUE.
LPEAD = .TRUE.
EDIFF = 1E-8
IBRION = -1
NSW = 0
```

安装案例 `requirements.txt` 中的依赖，加载 VASP 环境并准备 POTCAR 后，运行 `qsub job.pbs`。作业先检查电子计算，再调用分析脚本；已有输出时运行 `python3 postprocess.py` 即可。

## 如何读结果

在 OUTCAR 中找到 `MACROSCOPIC STATIC DIELECTRIC TENSOR (including local field effects in DFT)`，不要误取前面的独立粒子张量。该张量无量纲。本例得到：

$$
\epsilon_\infty =
\begin{pmatrix}
10.579637 & 0 & 0 \\
0 & 10.579637 & 0 \\
0 & 0 & 10.579637
\end{pmatrix}.
$$

Born 有效电荷描述原子位移引起的极化响应，和 [Bader 净原子电荷](../电子结构与成键/VASPBader电荷分析.md)不是同一个量。硅的两个 Born 张量在输出精度内均为零，压电张量也为零；程序检查介电张量对称性、各向同性和 Born 电荷的声学求和规则。

本例采用 `ENCUT = 350 eV` 和较粗 k 网格，用于熟悉响应流程。定量结果应在目标结构上测试截断能与 k 网格；极性材料若需要包含离子贡献，还需结合振动模和 Born 电荷，不能直接把这里的电子介电张量称为总静态介电常数。随频率变化的响应见[光学性质](VASP光学性质计算.md)。
