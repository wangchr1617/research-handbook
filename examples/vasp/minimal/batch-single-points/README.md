# 硅的批量单点与标签导出

参数与 PBS 步骤见[批量计算](../../../../notes/VASP/基础与准备/VASP批量计算.md)，数据定义见[训练数据准备](../../../../notes/VASP/动力学与机器学习/VASP训练数据准备.md)。准备授权 Si 势并加载软件依赖后，执行 `qsub job.pbs`。

`run.py` 顺序计算两个结构，`postprocess.py` 调用仓库的 `vasp2xyz.py`，交叉核对能量、力及位力后生成 `labeled-structures.xyz`。已有输出时可只运行后处理；单独复制案例到仓库外运行时，通过 `VASP2XYZ_SCRIPT` 指定导出器路径。
