# LAMMPS 中的 OPLS-AA 力场

**适用环境：通用（LAMMPS 输入文件）。**

OPLS-AA 的成键项包括谐和键长、键角势，以及 Fourier 形式的二面角势；非键项包括 Lennard–Jones（LJ）与 Coulomb 相互作用。下面的片段选择这些势函数形式及相应组合规则：

```text
atom_style full
bond_style harmonic
angle_style harmonic
dihedral_style opls
pair_style lj/cut/coul/long
pair_modify mix geometric
special_bonds lj/coul 0.0 0.0 0.5
```
