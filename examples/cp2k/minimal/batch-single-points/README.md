# 水分子的批量单点与标签导出

参数、PBS 操作和数据定义见[批量计算](../../../../notes/CP2K/批量计算与训练数据/CP2K批量计算.md)与[训练数据准备](../../../../notes/CP2K/批量计算与训练数据/CP2K训练数据准备.md)。加载 CP2K 和 Python 依赖后，执行 `qsub job.pbs`；所需基组与势函数从 CP2K 安装目录读取，不随案例分发。

`run.py` 顺序计算两个结构，`postprocess.py` 检查 SCF、能量与力，生成 `batch-results.json` 和 `labeled-structures.xyz`。已有输出时可只运行后处理。
