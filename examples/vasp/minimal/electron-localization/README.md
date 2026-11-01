# 硅的电子局域函数

参数、PBS 操作与结果解释见[笔记](../../../../notes/vasp/VASP电子局域函数.md)。准备授权 Si 势，加载 VASP、MPI、Multiwfn 及 `requirements.txt` 中的 Python 依赖后执行 `qsub job.pbs`。

`postprocess.py` 检查电子计算，`analyze.py` 调用 Multiwfn 导出 `elf.cub`，`plot.py` 绘制实际网格切面。已有 `ELFCAR` 时运行 `python3 analyze.py` 即可重画，无需重新计算 VASP。
