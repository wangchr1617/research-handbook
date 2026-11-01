# 硅的简谐热容

配套[笔记](../../../../notes/vasp/VASP热容计算.md)说明单位、热容和热力学输出。目录中的结构、位移、VASP 输入与声子谱案例相同，附 Phonopy 配置和 PBS 作业脚本。

准备授权 Si POTCAR，加载 VASP、MPI、Phonopy 后执行 `qsub job.pbs`。如已完成[声子谱案例](../phonon-dispersion/)，可直接使用其中的 `thermal_properties.yaml`，无需重复计算受力。

绘图依赖见 `requirements.txt`；后处理自动生成 `si-heat-capacity.png`。已有提取数据时可单独执行 `python3 plot.py` 重画，`--output` 可指定文件名。
