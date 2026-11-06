# GeTe 的熔融—淬火—退火轨迹

**适用环境：macOS / Linux，CPU 计算。**

原理、公式、模型和结果判据见[相变存储：从GeTe熔融淬火到晶化判据](../../../notes/材料应用/相变存储/相变存储：从GeTe熔融淬火到晶化判据.md)。本例依次生成结构、运行计算、提取数据并绘图。

## 输入与程序

参数文件为[phase-change.json](../../../inputs/materials/phase-change.json)，结构、INCAR 或分子/动力学输入由[运行器](../../../scripts/materials/run_case.py)中同名任务函数生成。以下为该参数文件的内容：

```json
{
  "case": "phase-change",
  "schema_version": 1,
  "a_A": 6.0,
  "repeat": [
    2,
    2,
    4
  ],
  "rattle_A": 0.08,
  "seed": 271828,
  "encut_eV": 300,
  "dt_fs": 2.0,
  "coordination_cutoff_A": 3.3,
  "stages": [
    {
      "name": "melt",
      "steps": 300,
      "start_K": 2000,
      "end_K": 2000
    },
    {
      "name": "quench",
      "steps": 400,
      "start_K": 2000,
      "end_K": 300
    },
    {
      "name": "anneal",
      "steps": 300,
      "start_K": 600,
      "end_K": 600
    }
  ]
}
```

运行后可以在每个子任务目录直接检查 `POSCAR/INCAR/KPOINTS`、`job.inp` 或 `in.lammps`。软件与 Python 环境选择见[公共运行说明](../../../notes/材料应用/本机运行与结果检查.md)。

## 从仓库根目录运行

```bash
bash scripts/materials/run_local.sh phase-change \
  --output _validation_runs/materials-user/phase-change
```

默认顺序运行，VASP 使用 1 个进程；`--threads 2` 控制相关程序的线程环境。输出目录已存在时脚本会停止。若是原参数、原输入的中断续跑，使用：

```bash
bash scripts/materials/run_local.sh phase-change \
  --output _validation_runs/materials-user/phase-change --resume
```

续跑会核对并复用输入、输出指纹一致的已登记子任务，运行未登记的任务。结构收敛或轨迹步数检查报错时，先检查对应子任务的日志。修改参数、赝势或结构后使用新目录。授权 PAW 势只在本地工作目录拼接，不加入公开数据。

## 正常停止与分段续算

若已有正常停止且电子收敛的 MD 短段，可补足原阶段步数：

```bash
bash scripts/materials/run_local.sh phase-change \
  --output _validation_runs/materials-user/phase-change --resume --continue-md
```

`--continue-md` 仅用于本例的受控短段：核对正常停止证据，原样衔接 `CONTCAR`，从 `REPORT` 恢复随机数状态，并保留剩余步数及降温斜率；后续阶段仍按原参数运行。它会自动继续后续段和阶段，不是暂停开关。常规 `--resume` 不接受不满足总步数的短段。

## 输出与检查

| 文件 | 用途 |
| --- | --- |
| `curve.csv` | 实际输出提取的绘图数据，表头注明单位 |
| `results.json` | 物理量、模型和近似说明 |
| `provenance.json` | 输入参数、执行命令、耗时及输入/输出 SHA-256 |
| `result.png` | 从 `curve.csv` 生成的图 |
| 子任务目录 | 原始输入、程序日志与输出，仅保留在运行位置 |

VASP 检查正常结束标记、所有离子步的电子迭代数和所需的结构优化/轨迹步数；ORCA 检查正常结束、优化与频率；LAMMPS 检查结束标记和曲线。通过这些检查只说明本例的执行与定义成立，材料性质仍须按教程进行数值收敛与物理模型检查。

## 比较结构而不只看温度

本例完成全部三个阶段后，运行器调用[结构分析脚本](../../../scripts/materials/analyze_phase.py)，从实际原始输出提取部分 RDF、配位分布和 MSD。已有完整输出时也可单独执行：

```bash
bash scripts/materials/run_local.sh --phase-structure \
  _validation_runs/materials-user/phase-change
```

| 文件 | 定义 |
| --- | --- |
| `rdf.csv` | 理想晶态参考与各阶段末尾最多 50 帧的 Ge–Ge、Ge–Te、Te–Te 部分 RDF |
| `structure-results.json` | 可用半径、样本帧数、3.3 Å cutoff 下的分元素配位均值、标准差和分布 |
| `msd.csv` | 以首帧为参考、展开周期边界并扣除质量加权整体质心漂移的分元素 MSD |
| `structure.png` | Ge–Te RDF 与非稳态轨迹 MSD 的两幅图 |

RDF 半径限制在最短晶面间距的一半以内，当前盒子约为 3.464 Å；这主要覆盖第一近邻，不能凭这段有限半径证明长程无序。配位分析沿用 3.3 Å 的教学阈值，研究时需按原子对与 RDF 最小值检验 cutoff 敏感性。配位分布的标准差描述样本离散程度，帧间可能相关，不能把它当作独立样本的标准误。

MSD 的首帧时间设为零，曲线横跨升降温与退火阶段，分析脚本不拟合扩散系数。是否已经充分熔融、形成代表性非晶或发生晶化，仍应结合更大模型、多初态、较长时间及其他有序度指标判断。

返回[材料案例](../README.md)。
