# 硅的 RTA 晶格热导率

模型、PBS 步骤及近似范围见[笔记](../../../../notes/VASP/振动与热力学/VASP晶格热导率计算.md)。准备授权 Si 势，加载 VASP 和 Python 依赖后，执行 `qsub job.pbs`。

`run.py` 用 phono3py 生成 19 个受力任务并顺序计算；`postprocess.py` 建立二/三阶力常数、检查声子并计算 RTA 热导率，`plot.py` 绘图。已有全部输出时只运行后处理。三阶位移对距离截断、电子 k 网格、声子 q 网格和展宽需分别收敛。
