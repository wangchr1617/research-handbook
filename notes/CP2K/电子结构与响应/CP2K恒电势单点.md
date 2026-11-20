# CP2K 恒电势单点

**适用环境：CP2K 2026.2，支持在 macOS 或 Linux 本地运行。**

电极与电子库交换电子时，可以固定目标功函数，让 slab 的净电荷在自洽迭代过程中自动调整。CP2K 的 GCE 方法以平面平均 Hartree 势作为参考，并通过平面补偿电荷来屏蔽 slab 的净电荷。计算时功函数以 eV 为单位输入；若要将其换算到特定的电化学参比电极，还需另外约定电势零点。

## 一、用对称 Li slab 跑通计算

可以从 [CP2K 上游六原子 Li 回归输入](https://github.com/cp2k/cp2k/blob/support/v2026.2/tests/QS/regtest-gcscf/Li_gcscf.inp)入手：保留三维周期正交晶胞，使 slab 居中并沿 Z 方向留出真空层。原生输入在 `DFT` 下启用了 `PLANAR_COUNTER_CHARGE`，在 `DFT/SCF` 下启用了 `GCE`、对角化求解器和 Fermi–Dirac 展宽。

```bash
OMP_NUM_THREADS=1 cp2k.psmp -i Li_gcscf.inp -o Li_gcscf.out
```

在 Alkemie 中选择「CP2K 双功函数恒电势对照」模板，对同一构型分别设定 4.0 eV 和 4.5 eV 两个目标功函数。该微型测试采用 PBE 泛函、100 Ry 主截断能和 40 Ry 相对截断能。上游回归算例使用的是 PADE 泛函，适合用来独立核对程序行为；一旦更换泛函，就需要重新核对功函数和净电荷。

## 二、从输出核对功函数与净电荷

首先确认 CP2K 正常结束且 SCF 收敛，然后读取 `GCE work function [eV]`、`GCE WF-TWF [eV]` 和 `GCE charge [e]` 三个字段。其中净电荷为正表示 slab 处于缺电子状态。Alkemie 在本机跑出的双点对照结果如下：

| 目标功函数（eV） | 最终功函数（eV） | slab 净电荷（e） |
| ---: | ---: | ---: |
| 4.0 | 3.999999950 | +0.016252 |
| 4.5 | 4.500000002 | +0.196645 |

核对时应重点关注 SCF 末端的功函数残差，以及同一几何构型下净电荷是否随目标功函数单调变化。另外需要注意，CP2K 2026.2 原生日志末尾名为 `GCE free energy` 的字段，在对应源码中实际打印的是电荷与功函数之积；因此用巨正则能量做横向比较时，务必同时核对总能量项、参考电荷、符号约定和单位。

本算例仅用于验证输入生成与结果解析。若要开展定量的电极体系研究，还需分别检验真空层厚度、补偿电荷平面位置、截断能、电子展宽以及有限尺寸效应，并明确隐式溶剂模型和参比电极的换算方式。

## 参考资料

- [CP2K 2026.2 的 GCE 输入说明](https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL/DFT/SCF/GCE.html)
- [Grand Canonical Ensemble Approaches in CP2K for Modeling Electrochemistry at Constant Electrode Potentials](https://pubs.acs.org/jctcce/article/20/18/8214/163963/Grand-Canonical-Ensemble-Approaches-in-CP2K-for)
