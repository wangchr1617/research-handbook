# 硅的GW 准粒子能带

输入、操作与结果图见[笔记](../../../../notes/vasp/VASPGW准粒子能带.md)。准备授权 `Si_GW` POTCAR，安装 `requirements.txt` 并加载 VASP 后执行 `qsub job.pbs`。`run.py` 在新目录完成各阶段，已有输出可用 `python3 postprocess.py` 或 `python3 plot.py` 分别检查、重画。

不要混用不同网格、能带数或截断下的波函数和筛选核。本例的较小参数用于学习完整流程，需进一步收敛后才能作定量分析。
