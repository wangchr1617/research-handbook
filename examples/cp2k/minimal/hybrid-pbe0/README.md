# 孤立水的 PBE0 单点与受力

输入、参数与结果图见[笔记](../../../../notes/CP2K/电子结构与响应/CP2K杂化泛函PBE0.md)。

加载带 Libint 的 CP2K，确认数据目录有 `BASIS_MOLOPT` 和 `GTH_POTENTIALS`，安装 `requirements.txt` 后执行 `qsub job.pbs`。`run.py` 在新目录中依次运行 PBE/PBE0，完成电子收敛、完整受力、净力及 HF 交换能检查。已有输出可执行 `python3 postprocess.py`；只重新绘图用 `python3 plot.py`。
