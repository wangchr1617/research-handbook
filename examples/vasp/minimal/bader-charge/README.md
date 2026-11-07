# NaCl 的 Bader 电荷与网格检查

输入参数、结果定义与图见[笔记](../../../../notes/VASP/电子结构与成键/VASPBader电荷分析.md)。按 `POTCAR.spec` 的顺序准备授权势，加载 VASP、VTST 的 `chgsum.pl`、Bader 和 Python 依赖后，执行 `qsub job.pbs`。

`run.py` 分别建立 `grid-96` 和 `grid-144` 并计算；`postprocess.py` 调用辅助工具、检查电荷及网格变化，再由 `plot.py` 输出 `nacl-bader.png`。已有两组输出时，可直接运行 `python3 postprocess.py`。工具不在 PATH 时设置 `CHGSUM_EXEC`、`BADER_EXEC`。

同一份 `96³` 价密度的 Hirshfeld、CM5 与 Bader 方法对照保存在[科学数据记录](population-comparison.json)，后处理步骤见[周期电荷分析](../../../../notes/CP2K/电子结构与响应/CP2K与Multiwfn的周期电荷分析.md#vasp-文件也能用于同类分析)。该对照比较分区定义，只有 Bader 提供了这里的双网格检查。
