# GPUMD 晶体能量、弹性与声子验证

NEP 拟合误差只描述样本上的统计偏差。将势用于晶体模拟前，可以依次检查平衡体积、弹性张量和声子。三项任务分别约束能量曲面的最低点、应变曲率和原子位移曲率。

## 一、按模拟目标选择要核对的曲率

| 任务 | GPUMD 入口 | 检查点 |
| --- | --- | --- |
| 能量–体积曲线 | `compute_cohesive` | 在同一晶相中采样最低点两侧，对照 DFT 或实验晶格参数。先核对能量和体积的每原子归一化 |
| 弹性 | `compute_elastic` | 用多个小应变对照张量和对称性，区分固定离子与弛豫离子。用未变形结构的残余应力判断是否在预期参考态 |
| 声子 | `compute_phonon` | 先优化并收敛超胞、位移幅度与路径。比较 Γ 点平移、软模及稳定性的参考结果 |

以训练数据中有同组成和晶相的结构开始，再选一个留出的体积或晶相复核。将 `compute_elastic 0.01` 视为 1% 应变的起点，再用更小应变检查线性范围。对多晶材料，可在张量验证后再求 Voigt/Reuss/Hill 平均。对带真空的模型，报告换算到体积或二维面积的约定。

## 二、先核对 GeTe 的位移数据，再比较频率

仓库的 [GeTe 声子 Notebook](../../examples/gpumd/nep-phonons/NEP声子谱计算.ipynb) 用 Phonopy 组织位移，分别读取参考力和用 NEP 计算受力。要判断两条谱的差异，先核对它们用了同一个原胞、超胞和位移清单。这个目录的 [POSCAR](../../examples/gpumd/nep-phonons/POSCAR) 含 1 个 Ge 和 1 个 Te，Notebook 示例单元设置的 $3\times3\times3$ 超胞应有 54 个原子，但随附的 [FORCE_SETS](../../examples/gpumd/nep-phonons/FORCE_SETS) 文件头写的是 128 个原子、4 组位移。运行前应找到与当前超胞和原子顺序匹配的参考力，或按同一位移清单重新生成。仅改文件头会保留错误的受力映射。

得到同条件的谱后，再看 Γ 点声学支和关心的软模。虚频可能来自结构失稳，也可能来自受力噪声和超胞截断。对关键模式逐步改变数值设置，并用 DFT 对应模式或畸变能量验证。准备动力学生产前，另在目标温压检查能量漂移和模型覆盖。

参考 [GPUMD 静态任务](https://gpumd.org/gpumd/input_files/run_in.html)、[弹性命令](https://gpumd.org/gpumd/input_parameters/compute_elastic.html)与[声子命令](https://gpumd.org/gpumd/input_parameters/compute_phonon.html)。
