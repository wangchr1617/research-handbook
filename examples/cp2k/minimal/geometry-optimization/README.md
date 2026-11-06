# CP2K 几何优化最小案例

配套[笔记](../../../../notes/CP2K/结构优化/CP2K几何优化.md)说明模型、参数与结果检查。目录提供 `structure.xyz`、`cp2k.inp`、`job.pbs` 和 `postprocess.py`。

在 PBS 集群加载 CP2K 环境，确认可找到 `BASIS_MOLOPT` 和 `GTH_POTENTIALS`，执行 `qsub job.pbs`。基组与势文件由软件安装提供，不随案例分发。
