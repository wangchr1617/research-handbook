# GPUMD 首个动力学与续算

在空目录准备 `model.xyz`、与其中元素匹配的势文件和 `run.in`。第一次运行选势已验证过的小周期晶体，先核对热力学量，再扩大到实际体系。以下语法对照 GPUMD 5.9.1 文档。

## 一、把生产输入缩成两段短跑

仓库的 [300 K 热输运输入](../../examples/gpumd/thermal-conductivity/300K/run.in) 先平衡再施加热驱动力。它用 1 fs 步长，第一段 100 万步对应 1 ns，第二段 2,000 万步对应 20 ns，势文件路径也依赖原机器。初次验证可以借用这种分段思路，用下面的短跑检查读入、系综切换和重启文件。示例的第一段用 NVT 检查固定晶胞下的温度调节，第二段用 NVE 暴露积分误差。

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

## 二、用 NVE 判断步长，再检查续算

先用 `thermo.out` 中的温度和晶胞核对第一段。进入 NVE 后，将每行的动能和势能相加，再除以原子数，观察总能是否持续漂移。若要判断漂移是否来自步长，从同一组位置和速度分别用 1 fs 和 0.5 fs 积分，相同的 2 ps 分别对应 2,000 步和 4,000 步。两段短跑只检查运行与积分，热导率等统计量还需要另做采样收敛。

第二段每 1,000 步写一次 `restart.xyz`，后一次会覆盖前一次。把文件复制到新目录并命名为 `model.xyz`，核对晶胞、元素顺序和速度字段。保留已读入的速度，续算脚本直接指定势、步长和下一段的系综及输出。若仍用 1 fs，最近一次存档位于从初始构型算起的 4 ps，合并分段输出时沿用该时间偏移。跨 `run` 的输入中，`time_step` 会继承，`ensemble`、`dump_thermo` 与 `dump_restart` 则按需要重写。

参考 [GPUMD 输入顺序](https://gpumd.org/gpumd/input_files/run_in.html)、[标准系综](https://gpumd.org/gpumd/input_parameters/ensemble_standard.html)及[重启输出](https://gpumd.org/gpumd/output_files/restart_xyz.html)。
