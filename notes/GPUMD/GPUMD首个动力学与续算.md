# GPUMD 首个动力学与续算

在空目录准备 `model.xyz`、与其中元素匹配的势文件和 `run.in`。第一次运行选势已验证过的小周期晶体，先核对热力学量，再扩大到实际体系。以下语法对照 GPUMD 5.9.1 文档。

## 两阶段短跑

先确认扩展 XYZ 含正确的晶胞、PBC、元素和位置。若加载 NEP，检查元素集合、势模型训练温压和结构类别。以下示意采用一份匹配的 `nep.txt`。结构应先完成弛豫，含异常近邻的输入先修正几何。

```text
potential nep.txt
velocity 300
time_step 1
ensemble nvt_nhc 300 300 100
dump_thermo 100
run 2000

ensemble nve
dump_thermo 100
dump_restart 1000
run 2000
```

在该目录运行 `gpumd`。步长为 1 fs，两个阶段各 2 ps，仅用于流程检查。耦合参数 100 是热浴时间常数与积分步长的比值。体相需要在外压下松弛时，按对称性设置 `npt_scr` 等压浴。带真空的片层通常固定含真空的方向。

## 判断输出与续算

- 先看 `thermo.out` 的温度、动能、势能、压力与晶胞。NVT 中热浴交换能量，NVE 段则用来比较每原子总能随时间的漂移。
- 用相同起始状态跑两档步长，比较相同物理时长。熔化、扩散或快速加载前，还需测试最大受力和原子最短距离。
- 续算时将 `restart.xyz` 复制为新目录的 `model.xyz`，检查晶胞和速度字段。读取保存的速度后，勿重新执行初始化速度的命令。保存独立的阶段文件和偏移后的时间轴。`ensemble` 与 `dump_restart` 要按阶段设置，输出命令的继承规则见文档。

参考 [GPUMD 输入顺序](https://gpumd.org/gpumd/input_files/run_in.html)、[标准系综](https://gpumd.org/gpumd/input_parameters/ensemble_standard.html)及[重启输出](https://gpumd.org/gpumd/output_files/restart_xyz.html)。
