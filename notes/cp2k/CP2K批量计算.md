# CP2K 批量计算

**适用环境：Linux（PBS 计算）；Windows / macOS / Linux（准备输入与分析结果）。**

批量计算的关键是让每个结构拥有独立目录，统一计算参数，并逐项检查结束标记和 SCF 收敛。准备输入时可先用 Multiwfn 建立一个可靠的单点模板，再替换坐标；不要为每个结构重新猜一套参数。

## 两结构最小案例

[案例目录](../../examples/cp2k/minimal/batch-single-points/)包含同一个水分子的参考结构和一条 O–H 键伸长 `0.02 Å` 的结构，用统一参数计算能量与力。

| 文件 | 用途 |
| --- | --- |
| [cp2k.inp](../../examples/cp2k/minimal/batch-single-points/cp2k.inp) | 共用 `ENERGY_FORCE` 模板，`CUTOFF=900 Ry`、`REL_CUTOFF=80 Ry` |
| [参考结构](../../examples/cp2k/minimal/batch-single-points/water-reference/structure.xyz) | 原始水分子坐标 |
| [伸长结构](../../examples/cp2k/minimal/batch-single-points/water-stretched/structure.xyz) | 一条键伸长后的坐标 |
| [run.py](../../examples/cp2k/minimal/batch-single-points/run.py) | 顺序运行，避免一次提交大量任务 |
| [job.pbs](../../examples/cp2k/minimal/batch-single-points/job.pbs) | PBS 作业入口 |
| [postprocess.py](../../examples/cp2k/minimal/batch-single-points/postprocess.py) | 检查计算并汇总标签 |

加载 CP2K 和案例 Python 依赖，确认安装目录能提供 `BASIS_MOLOPT` 与 `GTH_POTENTIALS` 后，在案例目录提交：

```bash
qsub job.pbs
```

作业依次建立 `runs/water-reference`、`runs/water-stretched`，复制模板和对应结构并运行。每个目录保存自己的 `cp2k.out` 与启动日志；已有输出时，脚本会停止，避免 CP2K 将新计算追加到旧输出中。

## 检查与汇总

后处理要求每个单点正常结束、SCF 收敛，并且能量与全部原子力均可解析。结果写入 `batch-results.json`，同时导出 `labeled-structures.xyz`。已有两组输出时，可直接执行：

```bash
python3 postprocess.py
```

不能仅凭输出文件存在或进程退出码为零就收集训练标签。若 SCF 失败，应先修复该任务；不要把失败结构的空值填成零。扩大批量时，先检查少量结构，再根据集群资源采用分批提交或作业数组，具体数组语法按 PBS 版本设置。

结构采样、单位转换和数据划分见[训练数据准备](CP2K训练数据准备.md)。
