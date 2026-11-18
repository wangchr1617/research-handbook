# Packmol 盐溶液与电荷平衡

要配一个约 1 mol/L 的 NaCl 模拟盒，先把浓度换成给定盒子里能放进去的整数粒子数。然后再决定水的个数、怎么保持电中性，以及把初始结构交给动力学程序时怎么验收。

## 一、从目标浓度反推整数粒子数

30 Å 立方盒体积为 $2.7\times10^{-23}$ L。用 $N_AcV$ 估算，1 mol/L 对应约 16.3 对 NaCl，取 16 对后，初始名义浓度约为 0.98 mol/L。水数由目标初始密度估算时，应把盐质量也计入。本例用 850 个水，方便后面核对密度和原子总数。

如果体系还有带电溶质，先按拓扑电荷确定补偿离子，再按盐的化学计量加入盐。补偿离子也会出现在最终浓度统计里，因此要说明报的是额外加入的盐，还是按所有离子计算的浓度。

## 二、装填 30 Å 水盒并核对分子顺序

准备 `water.xyz`、`na.xyz` 和 `cl.xyz`。水可用[周期水盒练习](../../examples/packmol-regions/README.md)中的三原子模板。两个离子模板各只有一个原子，在 XYZ 的前两行写原子数 `1` 和注释，第三行分别写 `Na 0 0 0` 或 `Cl 0 0 0`。

```text
tolerance 2.0
filetype xyz
output salt.xyz
seed 314159
pbc 30.0 30.0 30.0

structure water.xyz
  number 850
  inside box 0. 0. 0. 30. 30. 30.
end structure

structure na.xyz
  number 16
  inside box 0. 0. 0. 30. 30. 30.
end structure

structure cl.xyz
  number 16
  inside box 0. 0. 0. 30. 30. 30.
end structure
```

保存为 `salt.inp`，在模板所在目录运行 `packmol -i salt.inp`。用 21.2.3 试跑，输出 `salt.xyz` 有 2582 个原子，顺序为 850 个水、16 个 Na、16 个 Cl。按组成和初始盒体积估算的密度约为 1.00 g/cm³。构建力场拓扑后再核对总电荷和分子顺序。

## 三、平衡后再由体积反算浓度

用 [周期水盒的检查方式](空间分区、周期边界与拓扑对应.md)核对跨界最近接触，并确认拓扑中 850 个水、16 个 Na 和 16 个 Cl 的块顺序与 XYZ 相同。结构读入后先做几何最小化和所需的平衡。若在目标温压下体积改变，盐的粒子数仍是 16 对，应报告用平衡体积反算的浓度。分析离子配位、扩散或电导时，同时记录所用离子参数和采样区间。

语法见 [Packmol 官方指南](https://m3g.github.io/packmol/userguide.shtml)。
