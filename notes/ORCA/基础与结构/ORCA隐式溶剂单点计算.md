# ORCA 隐式溶剂单点计算

**适用环境：Linux + PBS 运行计算；Windows / macOS / Linux 可准备结构与分析结果。**

连续介质模型把环境的平均极化响应加入电子结构计算，适合比较同一模型下的溶剂效应。它不自动包含具体溶剂分子的配位与氢键网络。

本例对同一水分子几何分别做气相和 `CPCM(Water)` 单点计算，保持 PBE0/def2-SVP 与电子态一致。`run.py` 执行 `orca.inp` 和 `gas.inp`，分别保存输出与波函数，以比较环境模型带来的能量变化。

## 运行气相与 CPCM 两个计算

[最小案例](../../../examples/orca/minimal/implicit-solvation)包含：

- [orca.inp](../../../examples/orca/minimal/implicit-solvation/orca.inp)
- [structure.xyz](../../../examples/orca/minimal/implicit-solvation/structure.xyz)
- [gas.inp](../../../examples/orca/minimal/implicit-solvation/gas.inp)
- [run.py](../../../examples/orca/minimal/implicit-solvation/run.py)：组织计算步骤。
- [job.pbs](../../../examples/orca/minimal/implicit-solvation/job.pbs)：单节点 PBS 作业。
- [postprocess.py](../../../examples/orca/minimal/implicit-solvation/postprocess.py)：检查并提取结果。
- [requirements.txt](../../../examples/orca/minimal/implicit-solvation/requirements.txt)：Python 分析依赖。

在集群加载 ORCA 及其匹配的 MPI 环境。`ORCA_EXEC` 可指定 ORCA 驱动的绝对路径；作业使用一个进程、`%maxcore 1000`，PBS 申请 2 GB 内存。ORCA 由驱动启动，不在外面加 `mpirun`；基组由程序安装提供。

在案例目录安装 Python 依赖并提交：

```bash
python3 -m pip install -r requirements.txt
qsub job.pbs
```

作业结束后会自动执行后处理。重新分析已有输出时，可单独运行 `python3 postprocess.py`。PBS 中的软件加载方式与资源语法按集群配置调整；此例不需要多节点。

## 比较时保持哪些条件一致

| 选择 | 本例处理 | 扩展到研究时 |
| --- | --- | --- |
| 几何 | 两个环境使用同一结构 | 区分固定几何比较与分别弛豫后的能量差 |
| 模型 | CPCM 水 | 结合目标性质选择模型和参数 |
| 电子态 | 中性单重态 | 离子/自旋态先检查一致性 |
| 比较量 | 同几何电子能差 | 不直接命名为完整溶剂化自由能 |

## 这个能量差包含什么

后处理确认两个输出正常结束，并计算 E(CPCM)−E(gas)。本例气相约 −76.27350518 Hartree，CPCM 约 −76.28325375 Hartree，差约 −0.2653 eV。

CPCM 的变分能量包含溶质能量及其与溶剂反应场的相互作用。因此，上述差值包含了当前模型和几何下的自洽极化贡献。这里固定的是溶质几何，溶剂极化仍参与自洽；固定几何本身不能作为“非平衡溶剂响应”的判据。

如果要与实验溶剂化自由能比较，还需考虑模型中的其他项、标准态、热修正和构型取样。当前电子能差只回答了这组固定条件下的比较问题。

若反应涉及显式氢键、质子接力或金属配位，可考虑增加关键溶剂分子并采样构象，所有反应组分需使用一致方案。

进一步了解方法与文件规则，可看[ORCA 基础知识](ORCA基础知识.md)。参考：[ORCA 隐式溶剂](https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/solvationmodels.html)。
