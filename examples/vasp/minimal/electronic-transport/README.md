# 硅的电子输运

输入、参数、PBS 流程及结果图见[笔记](../../../../notes/vasp/VASP电子输运与电子热导率.md)。准备授权 Si 势，加载 VASP 与 `requirements.txt` 中的 Python 依赖后，执行 `qsub job.pbs`。

`postprocess.py` 检查 VASP 输出，调用 BoltzTraP2 插值与积分，再由 `plot.py` 绘制 `κe/τ`。已有输出时运行 `python3 postprocess.py`，无需重算 VASP。`BTP2_EXEC` 可指定 `btp2` 的绝对路径。
