# fcc LJ 晶格扫描

输入、参数与真实结果图见[笔记](../../../../notes/lammps/LAMMPS晶格常数与凝聚能.md)。加载 LAMMPS，安装 `requirements.txt` 后，在干净目录执行 `qsub job.pbs`。已有 `scan.dat` 时可执行 `python3 postprocess.py`。

选题参考单斌、陈征征、陈蓉《计算材料学》配套仓库第七章 7.3；输入与后处理重新编写，使用 256 原子静态模型，并以 ASE 独立核对能量。
