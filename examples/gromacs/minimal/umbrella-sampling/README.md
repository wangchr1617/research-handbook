# GROMACS伞形采样与平均力势最小案例

配套[笔记](../../../../notes/gromacs/GROMACS伞形采样与平均力势.md)说明方法、参数、结果与适用条件。

科学输入由 `stages.json` 组织，必要结构包含在坐标文件或各输入中。加载笔记指定的软件和外部数据，安装 `requirements.txt`，执行 `qsub job.pbs`。

`run.py` 执行各阶段，`postprocess.py` 检查原生输出并写 `results.json`；适合图示的结果另生成 `result.png`。基组、赝势、PAW 和原始运行输出不随案例分发。
