# CP2K 的 ADMM 杂化泛函

**适用环境：Linux + PBS 运行计算；Windows / macOS / Linux 可准备输入与分析结果。**

杂化泛函的精确交换常成为大体系计算瓶颈。ADMM 用较小辅助基组近似交换密度，并补充相应修正，降低部分 HFX 成本。

## 主基组与辅助基组承担什么任务

ADMM 近似的是精确交换的求值过程，杂化泛函的定义仍需另外指定。计算中保留两套基组：主基组描述轨道，AUX_FIT 描述辅助密度，各自引入的误差也要分别检查。

比较时应以相同几何、主基组、泛函比例和积分设置的 full-HFX 为基准。总能误差、相对能误差与力误差并不总是同步，尤其做优化和 AIMD 时要检查受力。

## 对照水分子的 full-HFX、cFIT3 与 FIT3

使用水分子 PBE0，主基组 DZVP-MOLOPT-SR-GTH，网格 900/80 Ry。分别计算不使用 ADMM、使用 cFIT3 和使用 FIT3 的三个分支；数据来自安装中的 BASIS_MOLOPT、BASIS_ADMM 和 GTH_POTENTIALS。

[案例目录](../../../examples/cp2k/minimal/admm-hybrid)包含以下科学输入：

[cfit3.inp](../../../examples/cp2k/minimal/admm-hybrid/cfit3.inp)、[fit3.inp](../../../examples/cp2k/minimal/admm-hybrid/fit3.inp)、[full.inp](../../../examples/cp2k/minimal/admm-hybrid/full.inp)、[stages.json](../../../examples/cp2k/minimal/admm-hybrid/stages.json)、[structure.xyz](../../../examples/cp2k/minimal/admm-hybrid/structure.xyz)。

结构写在坐标文件或各输入的原子/晶胞段；`stages.json` 列出计算阶段。配套 [run.py](../../../examples/cp2k/minimal/admm-hybrid/run.py) 顺序组织任务，[job.pbs](../../../examples/cp2k/minimal/admm-hybrid/job.pbs) 提交作业，[postprocess.py](../../../examples/cp2k/minimal/admm-hybrid/postprocess.py) 检查结果并绘图。

## 参数与提交

加载 CP2K，确保安装数据目录可找到所需基组与势文件，必要时设置 `CP2K_DATA_DIR`；`CP2K_EXEC` 指定程序。本例单进程、单线程顺序计算，数据文件不随案例分发。

| 输入 | 本例选择 |
| --- | --- |
| `HF/FRACTION` | 0.25，同时 PBE 交换系数为 0.75 |
| `AUXILIARY_DENSITY_MATRIX_METHOD/METHOD` | `BASIS_PROJECTION` |
| `ADMM_PURIFICATION_METHOD` | `MO_DIAG` |
| `KIND/BASIS_SET AUX_FIT` | cFIT3 或 FIT3 |
| `HF/MEMORY/MAX_MEMORY` | 每 MPI 进程的 HFX 模块预算，非总内存上限 |

其他 ADMM 变体还涉及交换修正与标度方案，应明确记录，避免将名称相似的近似混作一组。

在干净案例目录安装[Python 依赖](../../../examples/cp2k/minimal/admm-hybrid/requirements.txt)并提交：

```bash
python3 -m pip install -r requirements.txt
qsub job.pbs
```

PBS 中的资源语法和软件加载方式按集群调整。计算结束后自动执行后处理；若只分析已保存的结果，运行 `python3 postprocess.py`。各阶段独立保存输出，便于定位失败步骤。

## 辅助基组与变体怎样扩展

案例中的 cFIT3、FIT3 用于展示近似误差，保留它们才能复查现有数值。新任务还可从安装数据目录的 `BASIS_ADMM_UZH`、`BASIS_ADMM_MOLOPT` 等库选择与主基组相配的辅助基组。例如，UZH 库包含 O 的 `admm-dzp-q6` 和 H 的 `admm-dzp-q1`，也有更大的 `admm-tzp` 等条目；应逐元素核对具体名称、价电子数和覆盖范围，不按文件的新旧或名称长短直接决定精度。

每个实际 KIND 都需要相应 `AUX_FIT`。使用全电子主基组时选择全电子辅助基组，不能直接套用 GTH 价电子辅助基组。若某个 KIND 缺少合适的小辅助基组，可以研究用其主基组作为该 KIND 的辅助基组，但整体 ADMM 的交换修正与其他原子的误差仍需验证，不能据此宣称整套计算恢复为 full-HFX。

按下式理解常见 ADMM 思路，有助于区分主基组和辅助基组：

\[
E_x^{\mathrm{HF}}[P]
\approx E_x^{\mathrm{HF}}[\widetilde P]
+E_x^{\mathrm{DFA}}[P]-E_x^{\mathrm{DFA}}[\widetilde P].
\]

这里 \(P\) 是主空间密度矩阵，\(\widetilde P\) 来自辅助空间；具体投影、纯化和标度由变体定义。辅助基组中的 HF 交换加上交换修正，共同近似主空间的 HF 交换，最终还须按杂化泛函比例组合。不要在主泛函里再额外添加一遍上述修正。

当前 `ADMM_TYPE` 可成组设置变体对应的投影、纯化和标度参数。`EXCH_CORRECTION_FUNC` 则选择交换修正，与主交换泛函及交换算符保持一致。更换 OT、对角化、占据或范围分离方案时，要重新核对所选变体的兼容性，不能只保留一个空 ADMM 段而假定所有默认值都相同。设置原理和选型见[官方 ADMM 指南](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/admm.html)。

## 同时比较能量差与力差

相对 full-HFX，本例 cFIT3 与 FIT3 的能量差约为 −0.07695 与 −0.01526 eV；最大力分量差分别约 0.0907 与 0.0536 eV/Å。

在这组对照中，能量差较小的选择仍有可见的力差。因此应根据目标量和代表构型评估辅助基组，而非只按一个总能差排序。水分子太小，加速效果也应另在代表性较大体系上测量。

![CP2K的ADMM杂化泛函结果](../assets/admm-hybrid.png)

图由案例后处理脚本读取实际计算输出生成。

## 扩展到实际研究

从多种代表构型比较相对能、力与 SCF 稳定性，再扩展到优化或 AIMD。密度网格、主基组、HFX 筛选和辅助基组应分别控制。已掌握普通杂化输入可回看[PBE0 笔记](CP2K杂化泛函PBE0.md)，再选择适合目标精度的 ADMM 变体。

对于声子、NEB 或 AIMD，先在代表结构上比较 ADMM 与 full-HFX 的逐原子力及目标方向的力差，保留活动原子和分量，而不只比较合力或总能。接触拉伸、缺陷局域畸变等构型应纳入测试；平衡水分子的误差不能直接代表这些情况。

若怀疑能量与解析力不一致，可在固定晶胞下沿一个原子坐标作正负小位移，以相同 ADMM 变体、电子态及数值设置分别收敛，比较 $F_x$ 与 $-[E(x+h)-E(x-h)]/(2h)$。测试多个 h，区分有限差分截断误差与 SCF、网格噪声。这只检查所用近似内部的导数一致性，仍需 full-HFX 对照评估 ADMM 近似误差；变胞过程还要另查应力。

数值误差的分类与测试顺序见[网格与性质收敛](../../计算化学/数值积分网格与性质收敛.md)；ADMM 的 full-HFX 对照应保持同一泛函，避免把模型变化混入近似误差。

周期体系的截断半径、密度屏蔽、RI-HFXk 和每 MPI 进程内存预算，见[周期杂化泛函设置](CP2K周期杂化泛函的截断、屏蔽与内存.md)。ADMM 减小辅助交换空间，并不自动解决这些设置的收敛问题。

参考：[CP2K ADMM 参数](https://manual.cp2k.org/trunk/CP2K_INPUT/FORCE_EVAL/DFT/AUXILIARY_DENSITY_MATRIX_METHOD.html)。
