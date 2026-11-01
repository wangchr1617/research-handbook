# VASP单点能与受力最小案例

配套[笔记](../../../../notes/vasp/VASP单点能与受力.md)给出模型、输入、PBS 提交与结果判断。按 `POTCAR.spec` 准备授权 Si 势，加载 VASP、MPI 和 Python 环境后执行 `qsub job.pbs`。

计算后由 `postprocess.py` 检查结果。本例同时输出电荷密度和波函数，便于后续计算使用。
