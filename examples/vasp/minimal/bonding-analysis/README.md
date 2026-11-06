# 硅近邻键合分析

参数与操作见[笔记](../../../../notes/VASP/电子结构与成键/LOBSTER键合分析.md)。准备授权 Si `POTCAR` 和 LOBSTER 程序，将 `LOBSTER_EXEC` 指向该程序；加载标准 VASP 后执行 `qsub job.pbs`。LOBSTER 使用 OpenMP，与 VASP 的 MPI 启动方式不同。

`run.py --vasp-only` 只生成波函数，适合分开提交两阶段作业。已有 VASP 输出可直接运行 LOBSTER，再用 `python3 postprocess.py` 检查数据并绘制平均 −COHP。

`NBANDS = 8` 对应两原子各一个 s、三个 p 局域基函数；替换元素或基组后须同步调整。`lobsterin` 及输出格式应与所安装 LOBSTER 的随包手册核对。本例后处理只接受非自旋数据。
