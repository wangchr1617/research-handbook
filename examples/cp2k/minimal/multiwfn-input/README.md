# 用 Multiwfn 准备水分子单点计算

从 [structure.xyz](structure.xyz) 出发，使用 [multiwfn.in](multiwfn.in) 的菜单选择生成 [cp2k.inp](cp2k.inp)。详细步骤见[笔记](../../../../notes/CP2K/基础与准备/用Multiwfn生成CP2K输入文件.md)。

目录已附生成的输入，可直接检查并使用。要重新生成，先移走 `cp2k.inp`，再执行 `python3 prepare.py`。程序名可通过 `MULTIWFN_EXEC` 指定。

在 PBS 集群加载 CP2K 环境，确认数据目录包含 `BASIS_MOLOPT`、`POTENTIAL`，再运行 `qsub job.pbs`。作业结束后由 `postprocess.py` 汇总能量与收敛情况。

本例为三个原子的 PBE/DZVP-MOLOPT-SR-GTH 孤立水分子，适合学习输入生成与作业提交。生产计算需测试基组、网格与盒长。
