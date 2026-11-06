# 硅的能量—体积曲线

按 [POTCAR.spec](POTCAR.spec) 准备授权 Si 势，加载 VASP、VASPKIT、MPI 及 Python 依赖后执行 `qsub job.pbs`。`run.py` 生成五个固定体积任务，`postprocess.py` 收集能量并调用 VASPKIT `205` 拟合，最后用 `plot.py` 生成 `si-eos.png`。

输入参数、归一化和结果判断见[笔记](../../../../notes/VASP/结构与能量/VASP能量体积曲线拟合.md)。已有计算结果时无需重新运行 VASP，执行 `python3 postprocess.py` 即可重新拟合与绘图。
