# CASTEP 光学介电与偏振方向

电子光学谱需要均匀 k 网格上的跃迁矩阵元。带结构可以提示某个能窗有哪些态，谱的强度还取决于占据、矩阵元和偏振方向。先用 Si 做半导体流程，再用 Al 理解金属低能响应。

## 从自洽态到光学谱

复制[Si 单点输入](CASTEP首个单点计算.md)到新目录，保留已收敛的基态参数。在 `si.cell` 加 `SPECTRAL_KPOINT_MP_GRID : 12 12 12`，将 `si.param` 中的单点任务改成下段。这里的网格和空带数用于试跑，须按目标能窗收敛。

```text
TASK : SPECTRAL
SPECTRAL_TASK : OPTICS
SPECTRAL_NBANDS : 16
```

运行 `castep si`，检查 `si.bands` 和含光学矩阵元的 `si.ome_bin`。若使用兼容版本的 OptaDOS，在同一目录保存 `si.odi` 并运行 `optados si`。

```text
TASK : OPTICS
JDOS_SPACING : 0.05
JDOS_MAX_ENERGY : 10
OPTICS_GEOM : POLYCRYSTALLINE
```

示例用 0.05 eV 的能量步长，分析到 10 eV。打开 `si_epsilon.dat`，按三列读取光子能量、介电函数实部和虚部。分别加密谱网格、增加空带数和改变展宽，比较虚部峰位和相对强度，以及实部在低能区是否稳定。报告是否使用了剪刀修正。

## 偏振与低能响应

对低对称晶体按晶轴分别计算偏振响应，报告坐标系。若体系是带真空的二维片层，比较前说明所用厚度或按片层极化率表达，避免真空高度改变表观介电常数。

金属低能区还需考虑带内贡献及其阻尼参数。半导体的独立粒子光学吸收边会受带隙近似影响，间接跃迁、激子与温度效应需要匹配的模型。比较静态介电常数时应区分电子部分和离子响应。

公开练习见 [CASTEP 光学教程](https://castep-docs.github.io/castep-docs/tutorials/Optics/Optics/)与[谱计算关键词](https://castep-docs.github.io/castep-docs/documentation/Spectral/keywords/)。
