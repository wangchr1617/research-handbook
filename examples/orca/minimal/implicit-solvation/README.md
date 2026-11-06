# ORCA隐式溶剂单点计算最小案例

配套[笔记](../../../../notes/ORCA/基础与结构/ORCA隐式溶剂单点计算.md)说明方法、参数与检查。

主要输入为 `orca.inp`、`structure.xyz`、`gas.inp`。加载笔记指定的软件与外部数据后，执行 `qsub job.pbs`；作业调用 `run.py` 和 `postprocess.py`。

Python 依赖见 `requirements.txt`。原始计算输出、基组、势与力场数据不随案例分发。
