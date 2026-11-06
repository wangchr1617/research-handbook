# NaCl 的差分电荷密度

参考态、参数、PBS 步骤和结果图见[笔记](../../../../notes/VASP/电子结构与成键/VASP差分电荷密度.md)。准备按 `POTCAR.spec` 排列的授权势，加载 VASP、Multiwfn 与 Python 依赖后，执行 `qsub job.pbs`。

`run.py` 分别计算整体和两个固定位置的中性周期片段；`postprocess.py` 检查网格与结构、调用 Multiwfn 相减并检查电子数，`plot.py` 绘制实际网格切面。已有三组输出时运行 `python3 postprocess.py`。工具不在 PATH 时设置 `VASP_EXEC`、`MULTIWFN_EXEC`。
