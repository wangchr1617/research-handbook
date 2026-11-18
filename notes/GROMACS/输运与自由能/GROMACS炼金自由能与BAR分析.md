# GROMACS 炼金自由能与 BAR 分析

**适用环境：Linux + PBS 运行计算；Windows / macOS / Linux 可准备输入与分析结果。**

把水盒中的 Ar 从正常相互作用逐步变为与环境去耦，能得到这条去耦分支的自由能差。与伞形采样沿距离设置偏置不同，这里改变的是哈密顿量中的 λ。下面沿五份输入和 BAR 输出核对，每个状态改了什么、总自由能对应哪个方向，以及短采样怎样影响解读。

## 一、为什么检查相邻 λ 态的重叠

自由能差需要相邻 λ 态的能量分布有重叠。BAR 利用正反方向的能量差统计，通常比仅看平均 dH/dλ 更直接地暴露重叠不足；误差还受相关时间与平衡影响。

去耦粒子的 Lennard–Jones 相互作用时，普通线性缩放可能在端点出现奇异采样，soft-core 改变短程插值来缓解该问题。带电粒子还涉及电荷路径、长程静电与有限尺寸修正，不能照搬中性粒子方案。

## 二、逐步去耦一个中性 Ar 粒子

在相同水盒中放一个中性 LJ Ar，使用 λ=0、0.25、0.5、0.75、1 五个状态，从全相互作用逐步去耦至无溶质-环境相互作用。电荷始终为零，只改变 vdW；每态独立最小化后运行 10 ps；未进行充分的 NPT 密度预平衡，这也是本例仅用于流程演示的原因之一。

打开首末两份 MDP，可见 `couple-lambda0 = vdw-q`、`couple-lambda1 = none`，`init-lambda-state` 由 0 变到 4。本文的去耦方向是 $G_{\lambda=1}-G_{\lambda=0}$。若要求同一对端点的反向耦合自由能，要将这个差值换号。若要报告溶剂化或结合自由能，还要按目标定义把其他分支和标准态项纳入。

[案例目录](../../../examples/gromacs/minimal/alchemical-free-energy)包含以下科学输入：

共用最小化参数为 [em.mdp](../../../examples/gromacs/minimal/alchemical-free-energy/em.mdp)，阶段顺序见 [stages.json](../../../examples/gromacs/minimal/alchemical-free-energy/stages.json)。各窗口文件如下：

| 窗口 | 坐标 | 参数 | 拓扑 |
| --- | --- | --- | --- |
| l0 | [l0.gro](../../../examples/gromacs/minimal/alchemical-free-energy/l0.gro) | [l0.mdp](../../../examples/gromacs/minimal/alchemical-free-energy/l0.mdp) | [l0.top](../../../examples/gromacs/minimal/alchemical-free-energy/l0.top) |
| l1 | [l1.gro](../../../examples/gromacs/minimal/alchemical-free-energy/l1.gro) | [l1.mdp](../../../examples/gromacs/minimal/alchemical-free-energy/l1.mdp) | [l1.top](../../../examples/gromacs/minimal/alchemical-free-energy/l1.top) |
| l2 | [l2.gro](../../../examples/gromacs/minimal/alchemical-free-energy/l2.gro) | [l2.mdp](../../../examples/gromacs/minimal/alchemical-free-energy/l2.mdp) | [l2.top](../../../examples/gromacs/minimal/alchemical-free-energy/l2.top) |
| l3 | [l3.gro](../../../examples/gromacs/minimal/alchemical-free-energy/l3.gro) | [l3.mdp](../../../examples/gromacs/minimal/alchemical-free-energy/l3.mdp) | [l3.top](../../../examples/gromacs/minimal/alchemical-free-energy/l3.top) |
| l4 | [l4.gro](../../../examples/gromacs/minimal/alchemical-free-energy/l4.gro) | [l4.mdp](../../../examples/gromacs/minimal/alchemical-free-energy/l4.mdp) | [l4.top](../../../examples/gromacs/minimal/alchemical-free-energy/l4.top) |

结构写在坐标文件或各输入的原子/晶胞段；`stages.json` 列出计算阶段。配套 [run.py](../../../examples/gromacs/minimal/alchemical-free-energy/run.py) 顺序组织任务，[job.pbs](../../../examples/gromacs/minimal/alchemical-free-energy/job.pbs) 提交作业，[postprocess.py](../../../examples/gromacs/minimal/alchemical-free-energy/postprocess.py) 检查结果并绘图。

## 三、参数与提交

加载单节点 thread-MPI GROMACS，`GMX_EXEC` 指定 `gmx`。本例每窗口使用 2 个 OpenMP 线程，拓扑引用安装中的 AMBER99SB-ILDN/TIP3P；外部 MPI 构建需相应调整启动器。

| 设置 | 本例选择 |
| --- | --- |
| `free-energy/init-lambda-state` | 启用自由能并指定当前状态索引 |
| `couple-moltype ARG` | 只去耦所指定溶质 |
| `vdw-lambdas/coul-lambdas` | vdW 逐级变化，电荷路径不变 |
| `sc-alpha/sc-power/sc-sigma` | 0.5 / 1 / 0.3 nm，soft-core 参数 |
| `calc-lambda-neighbors=-1` | 输出本例所有态的能差以便分析 |

拓扑中 Ar 参数是简化模型定义，不是经过验证的通用气体溶解度参数。

在干净案例目录安装[Python 依赖](../../../examples/gromacs/minimal/alchemical-free-energy/requirements.txt)并提交：

```bash
python3 -m pip install -r requirements.txt
qsub job.pbs
```

PBS 中的资源语法和软件加载方式按集群调整。计算结束后自动执行后处理；若只分析已保存的结果，运行 `python3 postprocess.py`。各阶段独立保存输出，便于定位失败步骤。

## 四、读取 BAR 的自由能与误差

后处理丢弃前 2 ps，以原生 `gmx bar` 分析五组 dhdl 数据，保留各相邻态的详细结果、直方图与累计自由能。`bar-integral.xvg` 原生数值以 kT 表示，脚本显式转成 kJ/mol；图的横轴映射为实际 vdW λ。

本例去耦自由能约 −0.460 kJ/mol，原生分块误差约 0.319 kJ/mol。

用本机 GROMACS 2026.4、每窗口一个 OpenMP 线程复跑，BAR 给出 −6.413 kJ/mol，原生分块误差约为 0.675 kJ/mol。累计表的末点约为 −2.570872 $k_BT$；在 300 K 用 $RT$ 换算约为 −6.413 kJ/mol，与日志一致。复跑值与原记录的差距超过两次各自的分块误差，应保留两组结果。若要解释差异，后续需核对原运行条件、密度平衡、相邻态重叠以及延长采样后各段是否稳定。参见 [gmx bar 输出说明](https://manual.gromacs.org/current/onlinehelp/gmx-bar.html)。

总去耦自由能与原生分块误差保存在 `results.json`。这段短轨迹的分块误差尚未包含全部未平衡和慢相关影响，需要延长采样后再评估定量精度。

![GROMACS炼金自由能与BAR分析结果](../assets/alchemical-free-energy.png)

图由案例后处理脚本读取实际计算输出生成。

## 五、扩展到实际研究

正式任务检查相邻态重叠、端点行为、有效样本与正反方向一致性，必要时增加 λ 点并延长采样。溶剂化或结合自由能还需完整热力学循环、参考态和修正；当前只演示一个溶液去耦分支，没有把它直接称为完整结合自由能。

参考：[GROMACS 自由能与分析手册](https://manual.gromacs.org/current/index.html)。
