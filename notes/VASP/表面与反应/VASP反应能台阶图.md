# 吸附反应能台阶图

**适用环境：Linux + PBS（VASP）；Windows / macOS / Linux 可绘图。**

H/Al(111) 的吸附能已经按每个 H 算过。要画逐步吸附台阶，应该回到整胞能量，并把还没吸附的 H 留在气相参考里。这样三个台阶对应同一总组成，两个相邻台阶之差才是每一步的能量代价。

## 一、让三个台阶包含相同总量的氢

采用[吸附能笔记](VASP吸附能计算.md)的 H/Al(111) 模型，依次比较 `洁净表面 + H₂`、`H* + ½H₂`、`2H*`。星号表示吸附态，三个状态的 H 总数相同。相对能为

$$\Delta E_n=E(\mathrm{slab}+n\mathrm H)-E(\mathrm{slab})-\frac n2E(\mathrm H_2).$$

## 二、用已有四态输出重画台阶

[最小案例](../../../examples/vasp/minimal/energy-diagram)提供 [吸附态 INCAR](../../../examples/vasp/minimal/energy-diagram/INCAR.ads)、[洁净表面 INCAR](../../../examples/vasp/minimal/energy-diagram/INCAR.clean)、[H₂ INCAR](../../../examples/vasp/minimal/energy-diagram/INCAR.h2)、[结构](../../../examples/vasp/minimal/energy-diagram/POSCAR.half)、[k 网格](../../../examples/vasp/minimal/energy-diagram/KPOINTS.slab)和 [PBS 作业](../../../examples/vasp/minimal/energy-diagram/job.pbs)。按吸附能笔记准备授权势与 Python 依赖后，执行 `qsub job.pbs`。

若已经完成相同输入的吸附能案例，可在本例目录复用输出：

```bash
python3 run.py --reuse ../adsorption-energy
```

[后处理](../../../examples/vasp/minimal/energy-diagram/postprocess.py)会核对输入一致性与各态收敛，再由 [plot.py](../../../examples/vasp/minimal/energy-diagram/plot.py)生成台阶图。

![H 逐步吸附的反应能台阶图](../assets/al-h-energy-diagram.png)

## 三、从相邻台阶读逐步吸附能

三个台阶为 0、0.2387、0.6299 eV，单位为每个含两表面位点的晶胞；两步增量约 0.2387、0.3912 eV。例如第二步用 0.6299 减去 0.2387 eV。若从每 H 的平均值回算，先按各态的 H 数还原整胞吸附能，并在相减前保留足够位数。横线高度对应各状态，连接线只标明先后顺序。

图中是电子能差。若研究温度、压力或电极电位效应，应按具体体系加入零点能、熵和其他自由能修正，再绘制自由能台阶图。若要知道跨越两个状态需要多高的能量，还需沿指定路径寻找鞍点。见[CI-NEB 过渡态搜索](NEB过渡态搜索.md)。
