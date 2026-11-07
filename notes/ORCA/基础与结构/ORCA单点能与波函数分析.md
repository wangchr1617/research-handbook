# ORCA 单点能与波函数分析

**适用环境：Linux + PBS 运行计算；Windows / macOS / Linux 可准备结构与分析结果。**

单点计算在固定原子坐标上求解电子结构。它适合比较构型能量、准备波函数分析，也可用于优化后更高层级的能量评估。

## 固定水分子的几何，计算电子能

以中性单重态水分子为例，用 PBE0/def2-SVP 计算固定几何的电子能量。输入 O—H 距离为 1 Å；它是给定几何，不是本方法优化后的平衡结构。

单点能包含所选电子哈密顿量与核排斥项，但不自动等于焓或自由能。不同方法、基组、电子态或赝势下的绝对能量不宜直接混作同一参考。

## 准备并运行案例

[最小案例](../../../examples/orca/minimal/single-point)包含：

- [orca.inp](../../../examples/orca/minimal/single-point/orca.inp)
- [structure.xyz](../../../examples/orca/minimal/single-point/structure.xyz)
- [run.py](../../../examples/orca/minimal/single-point/run.py)：组织计算步骤。
- [job.pbs](../../../examples/orca/minimal/single-point/job.pbs)：单节点 PBS 作业。
- [postprocess.py](../../../examples/orca/minimal/single-point/postprocess.py)：检查并提取结果。
- [requirements.txt](../../../examples/orca/minimal/single-point/requirements.txt)：Python 分析依赖。

在集群加载 ORCA 及其匹配的 MPI 环境。`ORCA_EXEC` 可指定 ORCA 驱动的绝对路径；作业使用一个进程、`%maxcore 1000`，PBS 申请 2 GB 内存。ORCA 由驱动启动，不在外面加 `mpirun`；基组由程序安装提供。

在案例目录安装 Python 依赖并提交：

```bash
python3 -m pip install -r requirements.txt
qsub job.pbs
```

作业结束后会自动执行后处理。重新分析已有输出时，可单独运行 `python3 postprocess.py`。PBS 中的软件加载方式与资源语法按集群配置调整；此例不需要多节点。

## 方法、基组与电子态

| 设置 | 本例 | 含义与选择 |
| --- | --- | --- |
| 方法 | `PBE0` | 杂化 DFT；实际按目标性质与体系选择 |
| 轨道基组 | `def2-SVP` | 小型演示；正式能量需检查基组收敛 |
| SCF | `TightSCF` | 收紧电子自洽标准，不改变几何 |
| 电荷/多重度 | `0 1` | 中性闭壳层；其他体系先确定电子态 |
| 资源 | 1 进程、1000 MB 工作区 | 避免小体系过度并行；总 RAM 需留余量 |

## 从总能走向波函数分析

先在 `orca.out` 中确认电子收敛与正常结束信息，再读取 `FINAL SINGLE POINT ENERGY`。本例约为 −76.27350518 Hartree，可用于核对计算设置；它是当前方法下的电子总能，并非直接对应某个实验可观测量。

保留 `orca.gbw`，可用官方转换工具生成 Multiwfn 输入：

```bash
orca_2mkl orca -molden
```

再用 Multiwfn 打开 `orca.molden.input` 进行轨道、密度或静电势分析。绘制等值面时应报告等值、单位和数据来源。电荷分区有不同定义，不能把某一种原子电荷当作唯一可观测值。

更高层级单点可读取优化后的结构；换基组或电子态时，应按支持条件读取旧轨道并检查最终占据。

进一步了解方法与文件规则，可看[ORCA 基础知识](ORCA基础知识.md)。参考：[ORCA 输入与方法手册](https://www.faccts.de/docs/orca/6.1/manual/index.html)。
