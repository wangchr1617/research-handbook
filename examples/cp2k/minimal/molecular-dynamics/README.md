# CP2K 第一性原理分子动力学最小案例

配套[笔记](../../../../notes/cp2k/CP2K分子动力学.md)说明模型、参数与结果检查。目录提供 `structure.xyz`、`cp2k.inp`、`job.pbs` 和 `postprocess.py`。

在 PBS 集群加载 CP2K 环境，确认可找到 `BASIS_MOLOPT` 和 `GTH_POTENTIALS`，执行 `qsub job.pbs`。基组与势文件由软件安装提供，不随案例分发。
