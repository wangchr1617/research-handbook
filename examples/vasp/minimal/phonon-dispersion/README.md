# 硅的 Phonopy 声子谱

配套[笔记](../../../../notes/VASP/振动与热力学/VASP声子谱计算.md)说明有限位移、PBS 提交与结果检查。`POSCAR` 是两个原子的原胞，`POSCAR-001`、`POSCAR-002` 是 Phonopy 生成的 16 原子正负位移超胞。

准备授权 Si POTCAR，加载 VASP、MPI 和 Phonopy 4.x 后执行 `qsub job.pbs`。`run.py` 调用 Phonopy 生成位移并组织受力计算；`postprocess.py` 调用 Phonopy 导出 `band.yaml`、`thermal_properties.yaml`，并做数值检查。

`band.conf` 设置声子路径，`thermal.conf` 设置 q 网格和温度范围。正式计算需测试超胞、位移幅度、电子 k 网格与数值精度。

绘图依赖见 `requirements.txt`；后处理自动生成 `si-phonons.png`。已有提取数据时可单独执行 `python3 plot.py` 重画，`--output` 可指定文件名。
