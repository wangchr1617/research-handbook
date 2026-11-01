# VASP能带计算最小案例

输入参数、PBS 提交与 VASPKIT 操作见[笔记](../../../../notes/vasp/VASP能带计算.md)。按 `POTCAR.spec` 准备授权势文件，加载计算环境后执行 `qsub job.pbs`。

`check_vasp.py` 检查电子计算，`postprocess.py` 调用 VASPKIT；操作输入保存在 `vaspkit.in`，由 `run.py` 组织两个阶段。

绘图依赖见 `requirements.txt`；后处理自动生成 `si-bands.png`。已有提取数据时可单独执行 `python3 plot.py` 重画，`--output` 可指定文件名。
