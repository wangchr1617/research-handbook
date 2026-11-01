# 硅的静态电子介电响应

参数、文件说明和张量解释见[笔记](../../../../notes/vasp/VASP静态介电响应.md)。准备授权 Si 势并加载 VASP 与 Python 依赖后，执行 `qsub job.pbs`。

`postprocess.py` 检查计算并调用 `analyze.py`，后者生成 `dielectric-results.json`，检查立方硅的介电各向同性及 Born 电荷。修改材料时，应相应调整针对硅的检查。
