# 硅的准谐近似

模型、归一化和 PBS 步骤见[笔记](../../../../notes/VASP/振动与热力学/VASP准谐近似与热膨胀.md)。准备授权 Si 势，加载 VASP 和 Python 依赖后，执行 `qsub job.pbs`。

`run.py` 建立五个体积，每个体积进行一次未位移超胞静态计算和两次位移受力计算；`postprocess.py` 调用 Phonopy 建立力常数并拟合自由能，生成 `e-v.dat`、`qha-results.json` 和结果图。已有全部输出时只运行后处理。体积、位移和积分网格等可修改变量在对应脚本开头。
