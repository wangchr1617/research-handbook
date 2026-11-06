# 硅的 MLFF 训练与独立对照

阶段、文件传递和结果解释见[笔记](../../../../notes/VASP/动力学与机器学习/VASP机器学习力场.md)。准备授权 Si 势，加载支持 MLFF 的 VASP 及 Python 依赖后，执行 `qsub job.pbs`。

`run.py` 顺序完成 train、refit、run、reference 四阶段；`postprocess.py` 检查训练状态、预测无 DFT 调用，并与独立 DFT 构型比较。已有输出时可只运行后处理。数据库和二进制模型在运行时生成，不随案例分发。
