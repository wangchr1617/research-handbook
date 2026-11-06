# 硅的光学性质

参数、PBS 操作与结果图见[笔记](../../../../notes/VASP/响应与输运/VASP光学性质计算.md)。准备授权 Si 势，加载 VASP、VASPKIT 与 `requirements.txt` 的 Python 依赖后，执行 `qsub job.pbs`。

`postprocess.py` 检查电子计算，`analyze.py` 调用 VASPKIT 提取光学数据并运行 `plot.py`。已有输出时运行 `python3 analyze.py` 即可重新提取和绘图；只调整图形时运行 `python3 plot.py`。
