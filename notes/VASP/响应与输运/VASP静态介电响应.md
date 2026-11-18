# VASP 静态介电响应

**适用环境：Linux（PBS 计算）；Windows / macOS / Linux（输入编辑与结果分析）。**

金刚石硅有有限的电子介电响应，但它的 Born 有效电荷和压电张量为零。用这组三种输出，可以检查程序是否读对了张量，再决定自己的材料还需不需要计算离子贡献。`LEPSILON` 通过密度泛函微扰理论计算这些响应。[官方说明](https://vasp.at/wiki/index.php/LEPSILON)中的静态电子介电张量，不应与包含离子振动贡献的低频总介电常数混淆。

## 一、在固定硅原胞上计算电场响应

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

## 二、用晶体对称性核对三个响应量

在 OUTCAR 中找到 `MACROSCOPIC STATIC DIELECTRIC TENSOR (including local field effects in DFT)`，不要误取前面的独立粒子张量。该张量无量纲。本例得到：

$$
\epsilon_\infty =
\begin{pmatrix}
10.579637 & 0 & 0 \\
0 & 10.579637 & 0 \\
0 & 0 & 10.579637
\end{pmatrix}.
$$

Born 有效电荷描述原子位移引起的极化响应，和 [Bader 净原子电荷](../电子结构与成键/VASPBader电荷分析.md)不是同一个量。硅的两个 Born 张量在输出精度内均为零，压电张量也为零；案例脚本将介电张量与 $\operatorname{Tr}(\epsilon_\infty)I/3$ 对照，检验三个对角元是否相同、非对角元是否足够小；它还检查两个 Si 的 Born 张量各自接近零，以及逐分量相加是否闭合。换成低对称或极性材料时，应按其点群改用对应判据；Born 张量的总和可以为零，而单个原子的值有实际意义。

本例采用 `ENCUT = 350 eV` 和较粗 k 网格，用于熟悉响应流程。定量结果应在目标结构上测试截断能与 k 网格；极性材料若需要包含离子贡献，还需结合振动模和 Born 电荷，不能直接把这里的电子介电张量称为总静态介电常数。随频率变化的响应见[光学性质](VASP光学性质计算.md)。
