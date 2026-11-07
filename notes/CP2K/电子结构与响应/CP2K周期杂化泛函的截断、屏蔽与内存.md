# CP2K 周期杂化泛函的截断、屏蔽与内存

**适用环境：通用（输入与分析）；Linux 集群运行大体系。参数按 CP2K 2026.2 分支手册说明。**

从分子 PBE0 扩展到周期晶体时，除了交换比例，还要确定交换算符、布里渊区采样、积分屏蔽和内存预算。先用[水分子 PBE0 案例](CP2K杂化泛函PBE0.md)理解泛函定义，再逐项增加周期计算设置。

## 先区分三类近似

| 设置 | 控制什么 | 如何检查 |
| --- | --- | --- |
| HFX 交换算符与截断半径 | 精确交换采用的空间作用范围 | 增大半径，比较目标能差、力或带隙 |
| Schwarz 与密度矩阵屏蔽 | 哪些电子排斥积分可以忽略 | 收紧阈值并更换可靠初猜做对照 |
| ADMM、RI 及其辅助基组 | 怎样近似计算交换 | 固定泛函和主基组，与更严格设置比较 |

这些设置和 `MGRID/CUTOFF` 各管一层。提高平面波密度网格不能补回被屏蔽的交换积分；收紧 `EPS_SCF` 也不能消除辅助基组误差。

## 截断半径与晶胞几何

`HF/INTERACTION_POTENTIAL` 定义交换作用算符。`TRUNCATED` 在距离小于 \(R_c\) 时使用 \(1/r\)，超过半径时置零；`SHORTRANGE` 使用 \(\operatorname{erfc}(\omega r)/r\)。两者具有不同数学定义，不能把短程泛函的范围参数直接当作 PBE0 的数值截断半径。

对于常见的 Γ 点周期截断交换设置，要让截断球能放进晶胞。正交晶胞可以检查最短边长的一半；斜晶胞应检查相对晶面的垂直距离，而非直接取三个向量长度的最小值：

\[
V=|\mathbf a\cdot(\mathbf b\times\mathbf c)|,\qquad
h_a=\frac{V}{|\mathbf b\times\mathbf c|},\quad
h_b=\frac{V}{|\mathbf c\times\mathbf a|},\quad
h_c=\frac{V}{|\mathbf a\times\mathbf b|}.
\]

采用 \(2R_c<\min(h_a,h_b,h_c)\) 检查几何相容性，并为变胞过程保留余量。例如，12 Å 立方胞不宜直接配恰好 6 Å 的半径。增大半径可能需要扩胞；改变超胞后还应单独检查 Γ 点近似，不能把“截断球放得下”等同于采样已收敛。

6 Å 可作为一些体系的测试起点，定量判断应来自目标性质随半径的变化。反应物、产物与过渡态的能量比较采用一致的交换算符和截断设置，才能减少不受控的数值差异。参数单位和算符定义见[相互作用算符手册](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/INTERACTION_POTENTIAL.html)。

## 密度屏蔽为什么依赖初猜

`EPS_SCHWARZ` 越小，保留的积分通常越多，计算与存储代价越高。能量和受力分别涉及 `EPS_SCHWARZ` 与 `EPS_SCHWARZ_FORCES`，做优化、声子或 AIMD 时还要检查力误差。

`SCREEN_ON_INITIAL_P T` 利用初始密度矩阵进一步筛选积分。适合的准备方式是：先在相同结构、相容基组和赝势下完成较便宜的 PBE 计算，再用其收敛波函数启动 PBE0。下面仅展示第二步放入 `&DFT` 内的初猜片段，泛函和其余设置见完整案例：

```text
WFN_RESTART_FILE_NAME pbe-RESTART.wfn
&SCF
  SCF_GUESS RESTART
  # 其余 SCF 设置按目标任务填写
&END SCF
```

在输出中确认读入的是预期文件。结构 `.restart` 和电子 `.wfn` 用途不同，续算优化或 MD 时也要保留电子初猜。Γ 点的 `.wfn` 与 k 点的 `.kp` 重启格式不能互换。

较差的初猜可能在开始时就筛掉重要积分，SCF 随后达到阈值，也不代表屏蔽误差已经消失。小体系可先关闭初始密度屏蔽建立参照，再检查开启后的差异；大体系则选代表构型对照。

后续迭代会不会补回遗漏积分？这取决于设置。当前 `P_SCREEN_CORRECTION_FACTOR` 可在密度变化足够大时触发积分重算，但默认值 `0` 关闭这一纠正。应按实际启用状态判断，而非一概认为会自动补回，或永远不会更新。行为与默认值见[SCREENING 手册](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/SCREENING.html)。

## 第一轮很慢与内存预算

常规四中心 HFX 需要构造大量积分。能存入内存的部分可在后续 SCF 迭代复用，未存下的部分可能按需重算。因此第一轮显著较慢时，先查看进程状态和 HFX 输出，再判断是否卡住；不要仅凭两次 SCF 行之间的等待时间作结论。

`HF/MEMORY/MAX_MEMORY` 的单位是 **MiB，按每个 MPI 进程计算**，包含 HFX 模块的临时缓冲和辅助数组，余量才用于存积分。它没有限制整个 CP2K 进程的内存。一个节点上有 8 个 MPI 进程，每个设 2048 MiB，仅 HFX 预算就为 16 GiB，还要为其他模块、系统和并行通信留空间。混合 MPI/OpenMP 计算中，线程共享所属进程的预算，不再按线程数重复乘。

对常规 HFX，可观察 `Number of sph. ERI's calculated on the fly` 和 `Number of sph. ERI's stored in-core` 等统计，比较实际耗时和峰值内存后调整 MPI/线程组合。`MAX_DISK_SPACE` 可控制压缩四中心积分的磁盘缓存，代价包括磁盘空间与 I/O；不要将它当作无需测量的内存替代品。详见[HFX 内存参数](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/XC/HF/MEMORY.html)。

## 小晶胞可以使用 RI-HFXk

当前 CP2K 支持基于 RI 的 k 点杂化计算，不能沿用“杂化泛函一律只能算 Γ 点”的旧限制。小原胞加密 k 点通常值得与 Γ 点超胞方案比较；ADMM 也可与 RI-HFXk 组合，但 RI 辅助基组和 ADMM 辅助基组承担不同任务。

在 RI-HFXk 中，截断半径要与 k 网格对应的 Born–von Kármán 超胞相容，不再简单限定为原胞最短高度的一半。应按[官方 RI-HFXk 教程](https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/hartree-fock/ri_kpoints.html)设置 RI 基组、交换算符和采样；收敛 SCF 网格与画能带的高对称路径也分别处理。`KP_NGROUPS` 增加并行分组，同时增加部分内存开销，总 MPI 进程数需能被组数整除。常规四中心 HFX 的内存调优经验不能直接替代 RI 张量的内存检查。

## Kohn–Sham 矩阵稀疏警告

`The Kohn Sham matrix is not 100% occupied` 说的是矩阵块的存储范围，不是电子占据数不足。HFX 的非局域贡献可能超出按重叠矩阵建立的稀疏模式。

先检查 `QS/EPS_FILTER_MATRIX` 是否额外滤掉矩阵块，再比较更小的 `EPS_PGF_ORB`；`MIN_PAIR_LIST_RADIUS -1` 可要求单胞内所有原子对进入邻居关系，作为完整矩阵的对照。后者可能显著增加存储和运算。核对总能、力及 SCF 稳定性，不能只为消除警告而无限减小阈值，也不能因程序结束就忽略它。原因与处理顺序见[官方 HFX 警告说明](https://www.cp2k.org/faq:hfx_eps_warning)。

ADMM 的辅助基组与误差测试继续见[ADMM 教程](CP2K的ADMM杂化泛函.md)；跨层级能量比较见[计算层级切换](../../计算化学/计算层级切换与能量比较.md)。
