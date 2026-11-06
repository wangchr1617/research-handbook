# DFT+U最小对照

输入、参数及结果图见[笔记](../../../../notes/VASP/泛函与磁性/VASP的DFT加U计算.md)。

准备 `POTCAR.spec` 指定的授权赝势，安装 `requirements.txt`，加载计算环境后执行 `qsub job.pbs`。`run.py` 在新目录中完成两阶段计算；已有结果可执行 `python3 postprocess.py`，或 `python3 plot.py` 只重画结果。
