# NaCl 的 Bader 电荷与网格检查

输入参数、结果定义与图见[笔记](../../../../notes/VASP/电子结构与成键/VASPBader电荷分析.md)。按 `POTCAR.spec` 的顺序准备授权势，加载 VASP、VTST 的 `chgsum.pl`、Bader 和 Python 依赖后，执行 `qsub job.pbs`。

`run.py` 分别建立 `grid-96` 和 `grid-144` 并计算；`postprocess.py` 调用辅助工具、检查电荷及网格变化，再由 `plot.py` 输出 `nacl-bader.png`。已有两组输出时，可直接运行 `python3 postprocess.py`。工具不在 PATH 时设置 `CHGSUM_EXEC`、`BADER_EXEC`。
