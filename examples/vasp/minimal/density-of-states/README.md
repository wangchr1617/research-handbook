# VASP态密度计算最小案例

输入参数、PBS 提交与 VASPKIT 操作见[笔记](../../../../notes/vasp/VASP态密度计算.md)。按 `POTCAR.spec` 准备授权势文件，加载计算环境后执行 `qsub job.pbs`。

`postprocess.py` 检查计算输出，VASPKIT 操作输入保存在 `vaspkit.in`；能带案例由 `run.py` 组织两个阶段。

绘图依赖见 `requirements.txt`；后处理自动生成 `si-dos.png`。已有提取数据时可单独执行 `python3 plot.py` 重画，`--output` 可指定文件名。
