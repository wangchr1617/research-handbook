# Atomsk 超胞与点缺陷建模

要在 FCC 铝里做一个单空位，最好先保存完美超胞，再在副本上删除目标原子。这样既能复查删的是哪个位点，也能用同一晶格分析后续缺陷。下面在独立练习目录执行 Atomsk 命令，晶格常数 4.05 Å 和复制数 3 都是示例值。

## 一、先保留完美超胞，再删目标位点

```bash
atomsk --create fcc 4.05 Al -duplicate 3 3 3 al_bulk.xsf
```

用 [OVITO](../../OVITO/OVITO安装与基础操作.md) 打开 `al_bulk.xsf`，核对三个晶格矢量的长度约为 12.15 Å，FCC 常规胞的四个原子经复制后应有 108 个。检查准备移除的原子坐标，将下例的索引 1 换成所选原子的文件顺序索引。Atomsk 的索引从 1 开始。用可视化软件选点时，核对软件显示的是数组序号、文件顺序还是导入的粒子 ID。

```bash
atomsk al_bulk.xsf -remove-atom 1 al_vacancy.xsf
atomsk al_vacancy.xsf al_vacancy.lmp
```

输出结构应有 107 个原子，晶胞应与完美超胞相同。若要一次删除多个指定原子，先用 `-select` 建立选择集，再用 `-remove-atom select` 执行删除。逐个执行删除会使后续索引移动。

## 二、转换后用完美晶格核对缺陷

转换格式后重新核对盒矢量、坐标单位、元素和 LAMMPS 类型映射。读取 `al_vacancy.lmp` 的 LAMMPS 输入还需设置与所用势函数一致的单位、边界、原子样式和势参数。开始弛豫或动力学模拟前，先检查是否有异常近邻，并保留 `al_bulk.xsf` 作为 [Wigner–Seitz 分析](../../OVITO/Wigner-Seitz缺陷分析.md)的参考。若只检查刚生成、尚未弛豫的结构，用完美超胞作为参考，应有 107 个各占一个原子的位点、1 个空位和 0 个过量原子。若分析给出多重占据，先核对晶胞、参考结构和转换后的坐标。用于计算空位形成能时，完美和缺陷超胞应使用相同计算设置，另对超胞尺寸做收敛检查。

命令与选项见 [Atomsk 官方删原子教程](https://atomsk.univ-lille.fr/tutorial_removeatoms.php)和[选项说明](https://atomsk.univ-lille.fr/doc/en/options.html)。
