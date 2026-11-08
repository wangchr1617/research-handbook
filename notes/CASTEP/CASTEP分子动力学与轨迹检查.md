# CASTEP 分子动力学与轨迹检查

用短程 AIMD 学会检查时间步、每步电子收敛和续算。之后才将生产轨迹用于温度相关结构、扩散或其他统计量。起始结构、赝势和电子设置沿用已收敛的静态计算。

## 做短程 NVT 练习

在新目录复制弛豫后的输入，固定晶胞。可用 Si 超胞在 300 K 练习，少量原胞仅适合核对运行流程。下面是替换任务后需要加入的 `.param` 片段，电子结构参数仍由静态输入提供。

```text
TASK : MD
MD_ENSEMBLE : NVT
MD_THERMOSTAT : NOSE-HOOVER
MD_TEMPERATURE : 300 K
MD_DELTA_T : 1 fs
MD_NUM_ITER : 100
```

这组示意参数只覆盖约 0.1 ps。含氢、高温或有键重排的体系要单独测试时间步。若目标是外压下的体相密度，先选择兼容的变胞系综和压力边界。含真空薄片通常固定晶胞。

## 检查轨迹与续算

1. 检查 `.castep` 中每一步的电子收敛和异常受力。比对 `.md` 中的实际步数、时间、温度、能量、晶胞与坐标，确认解析工具使用正确单位。
2. 从同一平衡构型和速度分支做短 NVE，对比原步长和减半步长下相同物理时间的能量漂移。若减小步长没有改善，检查电子收敛、赝势、初态短接触或约束。
3. 续算时按版本说明从适合的检查点恢复相空间状态，核对接续处的步号、速度与晶胞。仅用末帧位置重新启动需要重新准备速度和热浴状态。
4. 生产段按所需物理量采样。液体的 RDF 检查体密度、周期边界和配位壳层。扩散用展开位移和多个时间原点，找长时线性区，再比较温度、体系尺寸和独立轨迹。

参考 [CASTEP MD 关键词](https://castep-docs.github.io/castep-docs/documentation/Molecular_Dynamics/keywords/)和[MD 概览](https://castep-docs.github.io/castep-docs/documentation/Molecular_Dynamics/overview/)。
