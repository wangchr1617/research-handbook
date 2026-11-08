# Packmol 盐溶液与电荷平衡

用 Packmol 为指定盐浓度生成初始周期盒。先由目标体积和浓度算整数粒子数，再核对电荷、模型密度和拓扑。

1. 例如 30 Å 立方盒体积为 $2.7\times10^{-23}$ L。若目标为 1 mol/L 的 1:1 电解质，盐的粒子对数约为 $N_A cV=16.3$，可取 16 对。此时装填阶段的名义浓度约为 0.98 mol/L。水的粒子数按所需混合物密度和盐质量估算。
2. 将阳离子、阴离子和水设成各自的结构块。每块使用同一周期盒的允许区域。多价离子用电荷数配平，若体系含已带电的溶质，先确定补偿离子，再加入目标量的盐。
3. 检查输出原子数、组成、拓扑电荷和周期最短接触。Packmol 的坐标输出不会自动生成部分电荷和力场参数。分子块顺序及模板内原子顺序要与拓扑一致。
4. 几何最小化并平衡到目标温压。若盒体积变化，报告由平衡体积反算的实际浓度。若做离子配位、扩散或电导，记录所用离子参数、密度、采样与电荷处理。

## 30 Å NaCl 水盒练习

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

语法见 [Packmol 官方指南](https://m3g.github.io/packmol/userguide.shtml)。
