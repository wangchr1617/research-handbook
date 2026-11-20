# VASP 约束分子动力学

**适用环境：Linux + PBS（VASP）；Windows / macOS / Linux 可绘图。**

若想观察分子在指定距离下如何转动或重排，可以约束一个集体变量，保留其余运动。本例只有两个 H 原子，把键长固定为起始值后，仍能通过改变键的朝向采样转动。

## 一、在 ICONST 里固定第 1、2 号原子的距离

[最小案例](../../../examples/vasp/minimal/constrained-md)采用 8 Å 盒中的 [H₂](../../../examples/vasp/minimal/constrained-md/POSCAR)，使用 [Γ 点](../../../examples/vasp/minimal/constrained-md/KPOINTS)。[ICONST](../../../examples/vasp/minimal/constrained-md/ICONST)只有一行：

```text
R 1 2 0
```

`R` 为原子间距离，`1 2` 是 POSCAR 中的原子序号，末尾 `0` 表示将距离约束到初始值 0.74 Å。[INCAR](../../../examples/vasp/minimal/constrained-md/INCAR)使用 `IBRION=0`、`MDALGO=1`、Andersen 温控，100 K、0.25 fs 步长和 8 步短轨迹。`SHAKETOL=1E-8` 控制约束校正精度，`RANDOM_SEED` 固定初始随机序列。

准备授权 H `POTCAR`，安装 [依赖](../../../examples/vasp/minimal/constrained-md/requirements.txt)，加载带相应高级 MD 功能的 VASP 后提交 [PBS 作业](../../../examples/vasp/minimal/constrained-md/job.pbs)：

```bash
qsub job.pbs
```

## 二、用 SHAKE 日志和实际坐标交叉验收

[后处理脚本](../../../examples/vasp/minimal/constrained-md/postprocess.py)会核对每一步的电子收敛以及 `REPORT` 中的 SHAKE 收敛记录，并从 `XDATCAR` 按最小周期映像直接计算原子间距。如果分子跨越了周期性边界，直接用包裹后的坐标相减会把短键误算成长键；核对无误后再由 [plot.py](../../../examples/vasp/minimal/constrained-md/plot.py) 绘图。

![H₂ 约束 MD 的键长](../assets/h2-constrained-md.png)

8 步均完成 SHAKE，保存轨迹中的最大键长偏差约 8×10⁻⁸ Å；该偏差也包含文本坐标截断误差。H₂ 去掉整体平移并加一个距离约束后只有两个活跃自由度，瞬时温度会有明显涨落，不能用如此短轨迹判断温控采样是否充分。

实际体系需先平衡，再检查步长、约束精度和统计长度。若要用约束平均力求自由能，还需多个反应坐标窗口、正确的约束力估计及相应几何修正；如何沿坐标安排窗口、记录约束力并重建曲线，可接着读[自由能窗口与 PMF](../../CP2K/动力学与反应/CP2K自由能窗口与PMF重建.md)。

参考：[VASP 约束 MD](https://vasp.at/wiki/Constrained_molecular_dynamics)、[ICONST](https://vasp.at/wiki/ICONST)。
