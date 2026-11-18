# LAMMPS 中的 OPLS-AA 力场

把有机分子的 OPLS-AA 参数迁到 LAMMPS 时，只照搬二面角系数还不够。沿三根键相连的两端原子还会发生非键相互作用，漏掉 1–4 缩放就会改变同一骨架的构象能差。可先用一条四原子链核对，再接回实际分子。

## 一、把势函数和非键规则一起迁移

下面只展示力场样式的设置。按参数来源和单位补齐截断距离、长程求解、拓扑与各项系数。

```text
atom_style full
bond_style harmonic
angle_style harmonic
dihedral_style opls
pair_style lj/cut/coul/long <cutoff>
pair_modify mix geometric
special_bonds lj/coul 0.0 0.0 0.5
```

`<cutoff>` 应替换为实际距离。`lj/cut/coul/long` 还需要相容的 `kspace_style`。若原参数文件已显式给出异类原子对系数，优先按原参数表核对，避免用默认混合规则覆盖来源不同的设置。参见 [LAMMPS 非键势说明](https://docs.lammps.org/pair_lj_cut_coul.html)。

## 二、用四原子链核对 1–4 缩放

对于教学拓扑 1–2–3–4，`special_bonds lj/coul 0.0 0.0 0.5` 把相隔一根或两根键的 LJ 和 Coulomb 权重设为零，把端点 1 和 4 的权重设为 0.5。这里数的是沿拓扑的成键距离。可以选两组固定坐标，先比同一四原子链的能量，再改变二面角复查相对能量。若能量差异常，先核对键表、参数单位和端点缩放，再检查二面角系数。对更复杂的旧输入，可沿[模型与输入核对](LAMMPS旧算例的模型与输入核对.md)追到生成后的拓扑。参见 [LAMMPS special_bonds](https://docs.lammps.org/special_bonds.html)。
