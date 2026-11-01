# VASP有限差分振动频率最小案例

硅原胞的 Γ 点振动，参数与 PBS 操作见[笔记](../../../../notes/vasp/VASP有限差分振动频率.md)。按 `POTCAR.spec` 准备授权势，加载 VASP 和 MPI 后执行 `qsub job.pbs`；从 `OUTCAR` 的频率与本征矢判断模式。
