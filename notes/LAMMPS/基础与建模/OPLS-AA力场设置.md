# LAMMPS 中的 OPLS-AA 力场

**适用环境：通用（LAMMPS 输入文件）。**

键结作用：harmonics 键长和键角势能，Fourier 扭矩势能

非键作用：LJ 势和 Coulomb 势

分别通过以下的 LAMMPS 参数设置：

```text
atom_style full
bond_style harmonic
angle_style harmonic
dihedral_style opls
pair_style lj/cut/coul/long
pair_modify mix geometric
special_bonds lj/coul 0.0 0.0 0.5
```
