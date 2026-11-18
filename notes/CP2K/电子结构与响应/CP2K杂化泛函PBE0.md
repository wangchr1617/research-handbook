# CP2K 杂化泛函 PBE0

**适用环境：Linux + PBS（带 Libint 的 CP2K）；Windows / macOS / Linux 可绘图。**

手上已有一份 PBE 结构，想知道改用 PBE0 会怎样改变优化方向，可以先在原构型上重算一次受力。仓库里的水分子对照只切换交换相关设置：PBE0 采用 25% Hartree–Fock 交换与 75% PBE 交换，保留全部 PBE 相关。先看同一构型上的差异，再决定是否用新泛函重新优化。

## 一、在同一水分子构型上换泛函

先用 [Multiwfn](../基础与准备/用Multiwfn生成CP2K输入文件.md)准备单点计算骨架，再调整交换相关部分。[最小案例](../../../examples/cp2k/minimal/hybrid-pbe0)提供 [structure.xyz](../../../examples/cp2k/minimal/hybrid-pbe0/structure.xyz)、[PBE 输入](../../../examples/cp2k/minimal/hybrid-pbe0/cp2k.pbe.inp)、[PBE0 输入](../../../examples/cp2k/minimal/hybrid-pbe0/cp2k.pbe0.inp)及 [PBS 脚本](../../../examples/cp2k/minimal/hybrid-pbe0/job.pbs)。

对比两份输入，改动集中在 `&XC`。如果从自己的 PBE 输入改起，保留原坐标、基组和网格，即可把它们排除为本轮力差的来源。PBE0 输入中，`&PBE` 的 `SCALE_X = 0.75` 与 `&HF` 的 `FRACTION = 0.25` 配套使用，避免重复计入交换。`SCALE_C = 1.0` 保持 PBE 相关。非周期水分子使用完整库仑算符；周期晶体需另外选择合适的交换作用形式和截断/采样设置。

这里的 25% 指交换项的混合系数，泛函、轨道基组与加速近似分别定义，见[HF 交换与范围分离](../../计算化学/交换相关泛函与HF交换的选择.md)。不能按 HF 百分比直接判断结构、带隙或自旋能差的精度。

本例使用 PBE 的 GTH 势、DZVP-MOLOPT-SR-GTH 基组及 900/80 Ry 网格，目的是在固定结构上演示泛函切换与受力检查。用于定量研究时，还应测试基组、网格、积分筛选精度及赝势选择。

确认 CP2K 版本信息含有 `libint`、数据目录可找到基组和势文件，安装 [Python 依赖](../../../examples/cp2k/minimal/hybrid-pbe0/requirements.txt)，在案例副本中提交：

```bash
qsub job.pbs
```

[run.py](../../../examples/cp2k/minimal/hybrid-pbe0/run.py)依次运行 PBE 与 PBE0。[检查脚本](../../../examples/cp2k/minimal/hybrid-pbe0/postprocess.py)核对电子收敛、完整原子受力、孤立分子净力，以及输出中实际出现的非零 HF 交换能，再调用 [plot.py](../../../examples/cp2k/minimal/hybrid-pbe0/plot.py)。已有输出可单独执行 `python3 postprocess.py`。

## 二、先确认交换项生效，再比较受力

![水分子在 PBE 与 PBE0 下的受力](../assets/water-hybrid-forces.png)

图中逐项比较同一构型、同一原子顺序下的九个受力分量。看整体净力可以发现明显的孤立分子数值异常，判断结构会往哪里走则要看各原子的分量。若关心 PBE0 平衡几何或频率，用 PBE0 重新优化后再做相应验收。判断方法精度需要与目标性质相符的参考。

本例直接计算四中心交换积分，未引入 ADMM。扩大体系后，可沿用[水分子的 ADMM 对照](CP2K的ADMM杂化泛函.md)评估加速近似，但需为辅助基组和近似误差另做对照。

周期晶体的截断半径、初始密度屏蔽和内存预算，继续见[周期杂化泛函设置](CP2K周期杂化泛函的截断、屏蔽与内存.md)。当前 CP2K 也有 RI-HFXk 路径，小原胞可按版本与目标任务选择 k 点方案，不必为使用杂化泛函一律扩成 Γ 点超胞。

参考：[CP2K 的 HF 设置](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF.html)、[交换作用算符](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/INTERACTION_POTENTIAL.html)。
