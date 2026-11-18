# 表面覆盖度与化学势

**适用环境：Linux + PBS（VASP）；Windows / macOS / Linux 可绘图。**

已经算出 H/Al(111) 的半覆盖和全覆盖吸附能，怎样判断在给定氢化学势下哪个表面更稳定？沿用原来的四组计算，把覆盖度不同的表面换到同一个化学势参考，再比较各条线的下包络。

## 一、把三个覆盖度换到同一氢参考

沿用[吸附能案例](VASP吸附能计算.md)的洁净、0.5 ML、1 ML 表面，定义 $\Delta\mu_\mathrm H=\mu_\mathrm H-\frac12E(\mathrm H_2)$。相对于同一洁净薄膜的大势差为

$$\Delta\gamma_n=\frac{E_\mathrm{ads}(n)-n\Delta\mu_\mathrm H}{A}.$$

本例只有一个表面吸附，面积 $A=14.205\ \mathrm{Å}^2$，因此除以 `A`。双面相同吸附模型应按实际吸附原子数与两面面积重新定义，不能直接照搬。

## 二、复用四态计算画出下包络

[最小案例](../../../examples/vasp/minimal/surface-phase-diagram)提供 [吸附态 INCAR](../../../examples/vasp/minimal/surface-phase-diagram/INCAR.ads)、[洁净态 INCAR](../../../examples/vasp/minimal/surface-phase-diagram/INCAR.clean)、[H₂ INCAR](../../../examples/vasp/minimal/surface-phase-diagram/INCAR.h2)、[结构](../../../examples/vasp/minimal/surface-phase-diagram/POSCAR.full)、[k 网格](../../../examples/vasp/minimal/surface-phase-diagram/KPOINTS.slab)和 [PBS 脚本](../../../examples/vasp/minimal/surface-phase-diagram/job.pbs)。按吸附能笔记准备授权势与依赖后执行 `qsub job.pbs`；已有相同输入的四态计算可执行：

```bash
python3 run.py --reuse ../adsorption-energy
```

[postprocess.py](../../../examples/vasp/minimal/surface-phase-diagram/postprocess.py)扫描每 H 的相对化学势 −1 至 0 eV，[plot.py](../../../examples/vasp/minimal/surface-phase-diagram/plot.py)绘出各候选相及其下包络。

![H/Al(111) 的表面大势差](../assets/al-h-surface-phase.png)

## 三、先比较下包络，再标相界

按吸附能笔记中的舍入值，洁净面与半覆盖在 +0.2387 eV 相交，洁净面与全覆盖在 +0.3150 eV 相交，半覆盖与全覆盖在 +0.3913 eV 相交。三个交点都超出本例 −1 至 0 eV 的扫描范围，区间内始终是洁净面最低。即使把扫描外推到 +0.3150 eV，此时半覆盖的大势差也比另外两个候选低，所以洁净面与全覆盖的交点仍不在下包络上。

实际相图需更全面的吸附位点、覆盖度与基底弛豫，以及适当的振动、气体或溶液自由能。这里的化学势尚未换算为温度、压力或电位。
