# Si 受约束 Dimer 鞍点搜索

结构、参数与结果图见[笔记](../../../../notes/VASP/表面与反应/VASPDimer鞍点搜索.md)。准备授权 Si `POTCAR`，安装 `requirements.txt` 并加载 VASP 后执行 `qsub job.pbs`。作业依次执行原生 Dimer 和三个自由度的有限差分振动检查；已有输出可执行 `python3 postprocess.py`。
