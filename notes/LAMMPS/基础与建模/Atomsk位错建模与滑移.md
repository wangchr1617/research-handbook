# Atomsk 位错建模与滑移

**适用环境：Linux（Atomsk 命令与 LAMMPS 计算）。**

以 Al 的 `1/2<110>{111}` 滑移系为例，先按滑移方向、滑移面法向和位错线方向确定模型坐标，再构建刃位错。

## 确定刃位错的方向

本例选择：

```text
X = [110]
Y = [-111]
Z = [1-12]
```

这样刃位错就是平行于 Z 轴，运动方向沿着 X 轴。

### 创建指定坐标轴的单胞

```text
atomsk --create fcc 4.046 Al orient [110] [-111] [1-12] Al_unitcell.xsf
```

### 扩胞

因为位错线是平行于 Z 轴的，所以 Z 方向不需要扩很大的倍数。

```text
atomsk Al_unitcell.xsf -duplicate 60 20 1 Al_supercell.xsf
```

### 构建刃位错有几种方式

1. 恒定原子数

```text
atomsk Al_supercell.xsf -dislocation 0.51*box 0.51*box edge Z Y 2.860954 0.33 -wrap Al_edge.cfg
```

`-dislocation` 后依次指定 XY 面内的位错位置、类型 `edge`、位错线方向 `Z`、滑移面法向 `Y`、Burgers 矢量长度和泊松比。`-wrap` 将盒外原子卷回盒内。

在模型的右边会产生一个台阶。

> 注：使用这种方法晶体丢失了在 XY 方向上的周期性，产生了两个影响：
>
> 1. 在模拟时需要固定盒子边界处的原子不动，否则在边界处可能会出现不合理的缺陷；
> 2. 如果位错需要在滑移面上运动，很快就会与固定的原子接触，阻止位错的传播。

2. 在滑移面之上插入一个新的半原子面

将第一种方法中的 `edge` 替换为 `edge_add` 即可。

```text
atomsk Al_supercell.xsf -dislocation 0.51*box 0.51*box edge_add Z Y 2.860954 0.33 -wrap Al_edge_add.cfg
```

这种方法在边界处不会有台阶出现。但是由于插入了一层原子，会导致体系沿着滑移方向 X 变大。
如果采用了周期性边界条件，会导致原子重叠。atomsk 会将 X 轴延长半个 Burgers 矢量。

> 注：该方法同样会丢失在 XY 方向上的周期性。

3. 在滑移面之下移除半个原子面

将第一种方法中的 `edge` 替换为 `edge_rm` 即可。

```text
atomsk Al_supercell.xsf -dislocation 0.51*box 0.51*box edge_rm Z Y 2.860954 0.33 Al_edge_rm.cfg
```

4. 将两块晶体堆叠在一起，上面比下面多半个原子面。

首先构建两个晶体块，底部块有 40 列原子，并且沿着 X 轴拉伸半个晶胞矢量 `0.5/40=0.0125`。
在这里通过 `-deform` 关键字并且泊松比设置为 0 实现沿着 X 轴的纯拉伸，否则 Y 方向会收缩。

```text
atomsk Al_unitcell.xsf -duplicate 40 10 1 -deform X 0.0125 0.0 bottom.xsf
```

顶部块有 41 列，沿着 X 轴压缩半个晶胞矢量 `0.5/41=0.012195122`。

```text
atomsk Al_unitcell.xsf -duplicate 41 10 1 -deform X -0.012195122 0.0 top.xsf
```

将两块晶体沿着 Y 轴叠加。

```text
atomsk --merge Y 2 bottom.xsf top.xsf Al_edge_bicrystal.cfg
```

合并后的初始结构沿 X 方向存在晶格失配，随后通过 `minimize` 弛豫形成刃位错。这一构造在 X 方向保留周期性，Y 方向仍为非周期。

### 同时构建多个位错

```text
atomsk Al_supercell.xsf -dislocation 0.251*box 0.251*box edge_add Z Y 2.860954 0.33 \
-dislocation 0.751*box 0.751*box edge_add Z Y -2.860954 0.33 Al_edge_dipole.cfg
```
