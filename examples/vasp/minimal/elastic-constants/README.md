# 硅的弹性常数

参数、PBS 操作和结果图见[笔记](../../../../notes/vasp/VASP弹性常数计算.md)。准备授权 Si 势并加载 VASP、VASPKIT、Python 依赖后，执行 `qsub job.pbs`。

`postprocess.py` 检查电子计算，`analyze.py` 调用 VASPKIT `203`，交叉核对 OUTCAR 与 `ELASTIC_TENSOR`，输出 `elastic-results.json` 并绘图。已有输出时运行 `python3 analyze.py` 即可；脚本中的立方对称性和平均模量公式针对本例硅。
