# CP2K 晶胞、振动模式与初始路径的文件接口

**适用环境：已有 Multiwfn、CP2K、Python、numpy 与 matplotlib 的 Windows、macOS 或 Linux。批处理命令使用 Bash。**

本例分别检查三件事：结构文件中的晶胞能否传入 CP2K，两种扩胞表示能否得到同一体系，以及振动/路径文件中的原子和序号能否正确对应。周期小模型使用自建斜晶胞中的水分子阵列；它用于格式与表示对照，不作为水或晶体物性的计算模型。

## 晶胞与输入生成

[plain.xyz](plain.xyz)为没有晶胞元数据的水结构；[lattice.xyz](lattice.xyz)与 [tv.xyz](tv.xyz)给相同坐标附上两种晶胞记法。三个向量为 `(8,0,0)`、`(1,7.5,0)`、`(0.5,0.3,9)` Å，基胞体积为 540 Å³。

把对应结构复制到独立目录并统一命名为 `structure.xyz`，再使用相应菜单：

| 目录或任务 | 结构来源 | 菜单 |
| --- | --- | --- |
| 普通 XYZ 默认行为 | `plain.xyz` | [plain.in](plain.in) |
| Lattice 晶胞 | `lattice.xyz` | [lattice.in](lattice.in) |
| Tv 晶胞 | `tv.xyz` | [tv.in](tv.in) |
| `MULTIPLE_UNIT_CELL 2 1 1` | `lattice.xyz` | [replicated.in](replicated.in) |
| 显式 `2×1×1` 扩胞 | `lattice.xyz` | [explicit.in](explicit.in) |
| 孤立分子、显式 NONE 与 OT | `plain.xyz` | [isolated.in](isolated.in) |
| XY 周期设置 | `lattice.xyz` | [slab.in](slab.in) |
| 振动输出骨架 | `plain.xyz` | [vib.in](vib.in) |

例如在 Lattice 工作目录执行：

```bash
multiwfn structure.xyz -silent < lattice.in > multiwfn.out
cp2k.psmp --check -i cp2k.inp
```

菜单文件和结构应放在所用工作目录，按实际路径调整。普通 XYZ 默认行为在 Multiwfn 2026.7.15 中会生成 `PERIODIC XYZ`；需要孤立分子时显式使用 `isolated.in`，不要把自动产生的盒子误当孤立边界。晶胞检查和不同任务的后续设置见[输入生成笔记](../../../../notes/CP2K/基础与准备/用Multiwfn生成CP2K输入文件.md)。

在 `replicated` 与 `explicit` 两个独立目录运行 CP2K 单点：

```bash
cp2k.psmp -i cp2k.inp -o scf.out
```

前者坐标仍为 3 个原子，`CELL` 和 `TOPOLOGY` 各有同一个重复数；后者已经有 6 个原子和 1080 Å³ 晶胞，不再附加重复数。两次原生 CP2K 2026.2 均读入 6 个原子、SCF 13 步收敛，能量约为 `−34.43979070004674 Ha`。

从仓库根目录提取对照，工作根目录的子目录名按上表的英文菜单名组织：

```bash
python examples/cp2k/minimal/structure-modes-path/analyze.py \
  --work-root /path/to/work --output /path/to/output/interfaces.json
```

[analyze.py](analyze.py)要求八种任务各有 `cp2k.inp`，并读取两种扩胞任务的 `scf.out`。[interfaces.json](interfaces.json)保存晶胞、边界、坐标和能量对照。语法通过只证明输入可解析；单点相符只检验两种表示，基组、网格和模型收敛另行判断。

## 读取已有真实水分子振动模式

[water-vibrations.mol](water-vibrations.mol)来自仓库[优化后水分子频率案例](../vibrational-analysis/README.md)的实际 CP2K 输出，使用 PBE/DZVP-MOLOPT-SR-GTH、280/40 Ry、10 Å 非周期盒、`DX=0.01 Bohr`。复现频率使用原案例的结构与输入；本目录 `vib.in` 用来检查生成器的振动打印选项。这组菜单在 Multiwfn 2026.7.15 中生成的 A、B、C 均为零向量，不能直接用于振动计算；先设置非零晶胞、按所选孤立边界居中结构，并检查盒长与数值收敛。CP2K 的 `--check` 可接受这份语法，仍不能证明晶胞有效。下述真实振型来自前述 10 Å 盒的原案例。

从仓库根目录运行：

```bash
python examples/cp2k/minimal/structure-modes-path/view_modes.py \
  --input examples/cp2k/minimal/structure-modes-path/water-vibrations.mol \
  --output-dir /path/to/modes --amplitude 0.15 --frames 24
python examples/cp2k/minimal/structure-modes-path/plot.py \
  --data /path/to/modes/vibration-modes.json --output /path/to/water-mode-vectors.png
```

[view_modes.py](view_modes.py)按 Bohr 读 `FR-COORD`，核对频率/模式/原子数及可选 Atoms、INT 字段，导出每个模式的 XYZ。`amplitude` 为最大原子显示位移，单位 Å，不能理解成温度或振动量子幅度。

已有的 [modes/vibration-modes.json](modes/vibration-modes.json)及三份 `mode-*.xyz` 保留这组三个实际振型；频率约为 1609.3、3716.5、3821.6 cm⁻¹，没有强度表。动画帧由正弦显示相位生成，不是动力学轨迹。MfakeG/GaussView 路线及晶胞扩展约定见[振动显示转换](../../../../notes/CP2K/动力学与反应/CP2K振动Molden与MfakeG显示转换.md)。

## 显式分段 NEB 初始路径

[anchors.json](anchors.json)复用[硅迁移案例](../neb/README.md)的两个端点，并将自建 [waypoint.xyz](waypoint.xyz)放在第 4 个副本。中间锚点只是几何示意：在端点平均结构上把移动原子的 y 坐标偏移 0.4 Å，没有赋予过渡态或能量含义。六个背景原子保持原位置。

```bash
python examples/cp2k/minimal/structure-modes-path/interpolate.py \
  --anchors examples/cp2k/minimal/structure-modes-path/anchors.json \
  --output-dir /path/to/new-path
```

[interpolate.py](interpolate.py)在锚点 1、4、7 之间生成共 7 个副本，保留给定锚点的序号；不自动旋转、对齐或选择周期映像。已生成的 [path/traj.xyz](path/traj.xyz)可预览，[path/BAND.inc](path/BAND.inc)列出全部副本，[path/path.json](path/path.json)保存相邻 Cartesian 距离。

将 `BAND.inc` 的内容合并到已有 `MOTION/BAND` 中，并把坐标文件放到 CP2K 运行目录；原有重复的 `NUMBER_OF_REPLICA` 和 `REPLICA` 列表相应替换。完成原子映射、周期映像和短接触检查后，再运行实际 NEB。上述路径文件只定义初始几何，能垒和过渡态由后续收敛计算确定。分段插值、sobNEB 与原生二分插点的区别见[路径准备笔记](../../../../notes/CP2K/动力学与反应/CP2K的NEB初始插点与路径检查.md)。
