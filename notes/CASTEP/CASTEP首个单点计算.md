# CASTEP 首个单点计算

用金刚石结构 Si 跑一次固定几何的电子自洽计算，熟悉结构、计算参数和主输出之间的对应关系。需要可用的 CASTEP 命令行程序，Materials Studio 用户也可在界面里建同一结构，再检查生成的输入。以下数值用于起步，后续按目标量测试收敛。

## 准备同名输入

在空目录保存 `si.cell`。这里用晶格常数 5.43 Å 的 FCC 原胞，两个原子的位置为分数坐标。三个原胞矢量长度是 $a/\sqrt{2}$，胞体积是 $a^3/4$，可用来核对结构导入。

```text
%BLOCK LATTICE_CART
ang
0.000 2.715 2.715
2.715 0.000 2.715
2.715 2.715 0.000
%ENDBLOCK LATTICE_CART

%BLOCK POSITIONS_FRAC
Si 0.000 0.000 0.000
Si 0.250 0.250 0.250
%ENDBLOCK POSITIONS_FRAC

SYMMETRY_GENERATE
KPOINT_MP_GRID : 6 6 6
```

保存 `si.param`。这里用 PBE、400 eV 截断与固定占据启动 Si 绝缘态自洽。运行前从输出核对发行版为 Si 选用的赝势。跨计算比较时，应保持同一势定义和价电子数，必要时显式指定 `SPECIES_POT`。

```text
TASK : SINGLEPOINT
XC_FUNCTIONAL : PBE
CUT_OFF_ENERGY : 400 eV
ELEC_ENERGY_TOL : 1e-7 eV
FIX_OCCUPANCY : TRUE
```

## 运行并核对

```bash
castep si
```

把 `castep` 换成本机实际可执行程序名。先用 `castep -help search cut_off_energy` 核对关键词。命令使用种子名 `si`，程序由此读取同名的两个文件。不要在同一目录用同一种子运行互不相干的作业。

打开 `si.castep`，依次核对程序版本、元素和价电子数、晶胞与 k 网格、截断、SCF 收敛及最终能量。原胞含两个 Si。做金属对照时，把固定占据设置改成与金属相容的占据方案并核对展宽，见 [Si 与 Al 能带对照](CASTEP的Si与Al能带对照.md)。下一步先做[截断与 k 点收敛](CASTEP截断与k点收敛.md)，再优化几何。

参考 [CASTEP 运行说明](https://www.castep.org/using_castep)、[Cell 关键词](https://castep-docs.github.io/castep-docs/documentation/Input_Files/cell_keywords/)及[输出文件](https://castep-docs.github.io/castep-docs/documentation/Output_Files/output_files/)。
