# 固定 c 的正交硅晶胞优化

参数、输入链接与结果说明见[笔记](../../../../notes/VASP/结构与能量/VASP固定晶格优化.md)。

准备授权 `POTCAR`，安装 `requirements.txt` 中依赖，确认 `job.pbs` 的 `VASP_EXEC` 指向对应扩展程序，然后 `qsub job.pbs`。在新目录运行 `run.py`，已有结果可单独执行 `python3 postprocess.py`。
