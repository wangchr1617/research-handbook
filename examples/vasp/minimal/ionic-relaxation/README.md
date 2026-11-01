# VASP原子位置优化最小案例

配套[笔记](../../../../notes/vasp/VASP原子位置优化.md)给出模型、输入、PBS 提交与结果判断。按 `POTCAR.spec` 准备授权 Si 势，加载 VASP、MPI 和 Python 环境后执行 `qsub job.pbs`。

计算后由 `postprocess.py` 检查结果。已有输出可单独运行 `python3 postprocess.py` 检查并重画图；绘图依赖见 `requirements.txt`。
