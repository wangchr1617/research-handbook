# ALTBC 计算

角度限制三体关联（angular-limited three-body correlation，ALTBC）考察近共线的三个原子：以 B 为中心，同时记录两侧 A–B 和 B–C 的距离。它回答的是：**同一局域环境中，一侧距离较短时，另一侧是否倾向于较长？** RDF 把原子对距离分别累积，ALTBC 则保留这两段距离的关联，适合分析 GeTe 等相变材料中的局域长短键交替。

本文使用 [altbc_analyzer 远程仓库](https://github.com/wangchr1617/altbc_analyzer)，接口按 0.2.0、提交 `26ae0ca0e9991340a92d0dd0b44064fba12316b8` 核对。程序读取原子坐标并输出距离对直方图；电子机制需结合文献及电子结构计算讨论。相变轨迹的准备见[从 GeTe 熔融淬火到晶化判据](相变存储：从GeTe熔融淬火到晶化判据.md)。

## 从 Peierls 畸变到局域长短键

Peierls 畸变的经典图像是一维、部分填充能带的等间距原子链：晶格发生周期性位移后，原本相同的间距变成短—长交替，能带在相关波矢处发生重构。电子能降低与晶格形变代价竞争，决定畸变是否稳定。这个图像强调电子与晶格的耦合，不能只凭出现两种距离便认定其能量来源。

GeTe 等三维硫属化合物常用 **Peierls-like distortion（类 Peierls 畸变）**描述近八面体环境中相对方向的长短键。以理想岩盐型六配位为参考，中心原子发生适当偏心位移可形成三短、三长的环境；在近共线 A–B–C 中，它表现为一短一长。液体或非晶中没有完整的一维平移周期，仍可保留这种局域关联。压力下 GeTe、GeSe 的研究用 ALTBC 追踪了这一关联的变化，并结合衍射与模拟讨论结构转变。[Fujita 等，2023](https://doi.org/10.1038/s41467-023-43457-y)

### 赝 Jahn–Teller 效应提供什么解释

赝 Jahn–Teller 效应（pseudo-Jahn–Teller effect，PJTE）描述不同电子态通过结构振动发生耦合、使高对称构型失稳的机制；它允许参考电子基态非简并。为理解其能量竞争，可在非简并参考态附近，用非简并微扰论写出一个单模示意模型：

$$
E(Q)\simeq E(0)+\frac12K_0Q^2
-\sum_{n>0}\frac{|F_{0n}|^2}{E_n-E_0}Q^2,
\qquad
F_{0n}=\left\langle0\left|\frac{\partial H}{\partial Q}\right|n\right\rangle.
$$

这里 $Q$ 是畸变坐标，$K_0$ 表示该模型中未计入所列态间耦合的回复力常数，$F_{0n}$ 是振电耦合矩阵元。二阶耦合项降低能量；有效曲率 $K_0-2\sum_{n>0}|F_{0n}|^2/(E_n-E_0)$ 为负时，参考位置沿该模式不稳定，高阶项决定后续势能面。该式用于说明机制，不能直接把 ALTBC 的峰间距代入求耦合常数。[Bersuker，PJTE 理论综述](https://doi.org/10.1021/cr300279n)

在 GeTe 中，Wang 等通过 DFT、机器学习势分子动力学和时间分辨 COHP 分析，将局域电子重排与 PJTE 联系起来。该工作讨论的是晶体铁电相变，不能直接替代非晶—晶态存储切换的动力学解释。[Wang 等，2026](https://doi.org/10.1103/w7ll-dsct)

Peierls 图像强调延展体系的电子—晶格失稳，PJTE 图像强调电子态间的振电耦合；两者都可用于讨论特定体系中的低对称结构，但需要与相应能量、电子态和振动证据对应。**ALTBC 提供的是局域几何统计**：离对角分布可支持长短距离关联的判断，机制归因还需畸变能量曲线、声子、轨道或成键分析。

## ALTBC 图如何定义、如何读

对中心 B 和两个不同的邻居像 A、C，定义

$$
r_1=|\mathbf r_A-\mathbf r_B|,\qquad
r_2=|\mathbf r_C-\mathbf r_B|,\qquad
\theta=\arccos\frac{(\mathbf r_A-\mathbf r_B)\cdot(\mathbf r_C-\mathbf r_B)}{r_1r_2}.
$$

周期体系的向量还包含晶格平移。代码先取两段距离都严格小于 `cutoff` 的邻居，再筛选 $\theta_{\min}\leq\theta\leq\theta_{\max}$。默认角窗为 155–180°，即中心两侧近乎相反的方向；它不是接近 0° 的同向邻居对。

若距离格区间记作 $I_i$，`counts` 模式的原始网格可概括为

$$
H_{ij}=\sum_t\sum_{B\in S_t}\sum_{A\ne C}
\mathbf1_{r_1,r_2<r_c}\,
\mathbf1_{\theta_{\min}\leq\theta\leq\theta_{\max}}\,
\mathbf1_{r_1\in I_i}\,\mathbf1_{r_2\in I_j}.
$$

$S_t$ 是第 $t$ 帧选定的中心原子集合，邻居还可按元素筛选。数学下标按两段距离书写；NumPy 数组存储为 `grid[y_bin, x_bin]`，图中横轴为 $r_1$、纵轴为 $r_2$。

| 分布特征 | 几何含义与判断 |
| --- | --- |
| 峰靠近 $r_1=r_2$ | 近共线两侧距离相近；距离大小仍需读坐标。 |
| $(r_s,r_l)$、$(r_l,r_s)$ 两个离对角峰 | 一短一长在同一三原子组中关联出现，符合类 Peierls 局域畸变的几何特征。 |
| 分布宽、峰不清晰 | 可能混合了热涨落、不同配位或不同化学环境；宜分元素、温度阶段和时间窗口比较。 |

**两个镜像峰是有序计数约定的结果。** 每个符合条件的无序邻居对同时贡献 $(r_1,r_2)$ 和 $(r_2,r_1)$；若落在同一个对角格中，该格也会增加两次。镜像峰不代表两个独立物相。示意上，2.7 Å 和 3.5 Å 的共线距离对会落在 $(2.7,3.5)$ 与 $(3.5,2.7)$ 附近，这组数值只是几何例子。

ALTBC 对整体转动不敏感，却也丢失了畸变方向。因此，局域长短键分裂、宏观极化以及长程晶体有序应分别检查。时间累积图还会混合静态畸变和瞬态振动；研究寿命或跳跃时，需要按中心原子追踪时间序列或计算时间关联函数。

### 代码中的归一化

本实现没有执行理想参考体系、径向壳层体积或角度相空间的归一化，因此输出是角窗内的**距离对直方图**，不能直接当作严格归一化的 $g^{(3)}$ 与其他程序逐值比较。

| `normalization` | `counts` 模式下的含义 | 适合的比较 |
| --- | --- | --- |
| `none` | $H_{ij}$，原始有序三体计数 | 核查累积数与输出完整性。 |
| `max`（默认） | 除以本图最高格计数 | 观察形状；不同图各自最高点都为 1，峰高不代表数量相同。 |
| `density` | 除以窗口内总计数及格面积 | 窗口条件下的概率密度，单位 Å⁻²；积分为 1，空图为 0。 |
| `per_center` | 除以各帧选定中心数之和及格面积 | 每中心的有序距离对密度，单位 Å⁻²；保留角窗内数量变化。 |

`per_center` 的分母包含没有有效三原子组的选定中心，其积分是每个中心在所选窗口内的平均有序三体数。另一个参数 `histogram_mode="occupancy"`（CLI 为 `--mode occupancy`）使每帧每格至多加 1，统计的是“该帧是否占据该格”，不等同于计数模式，也不支持 `per_center`。比较不同体系时应固定统计模式、筛选条件及归一化方式。

## 安装与命令行示例

以下命令在 macOS / Linux 终端执行，也可在已配置的 WSL 中使用。需要 Python 3.9 或更新版本；依赖包括 ASE、NumPy、pandas、Matplotlib 和 SciPy，随项目安装。这里新建独立环境，不修改已有 Conda 环境。

```bash
git clone https://github.com/wangchr1617/altbc_analyzer.git
cd altbc_analyzer
# 固定到本文核对的版本；需要新功能时再主动更新。
git checkout 26ae0ca0e9991340a92d0dd0b44064fba12316b8
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
altbc --help
```

下列相对路径都从 `altbc_analyzer` 仓库根目录出发。先用项目提供的结构分析 **Te–Ge–Te**：

```bash
altbc example/POSCAR --center Ge --neighbor Te \
  --cutoff 4.0 --theta-min 155 --theta-max 180 \
  --xmin 2.5 --xmax 3.8 --bin-width 0.02 \
  --mode counts --normalization per_center --dpi 600 \
  -o outputs/structure_ge_te.png
```

`--center Ge` 指 B 为 Ge；`--neighbor Te` 要求 A、C 都是 Te。省略 `--neighbor` 会混合所有邻居元素；省略 `--center` 会累积所有中心，解释化学环境时要保留这个区别。当前接口不能一次单独筛出 A、C 为两种不同指定元素的三体组。

轨迹使用 ASE 可读的多帧文件，例如项目的扩展 XYZ：

```bash
altbc example/test.xyz --trajectory --stride 1 \
  --center Ge --neighbor Te \
  --cutoff 4.0 --theta-min 155 --theta-max 180 \
  --xmin 2.5 --xmax 3.8 --bin-width 0.02 \
  --mode counts --normalization per_center --dpi 600 \
  -o outputs/trajectory_ge_te.png
```

`--trajectory` 读取多帧，`--stride 1` 保留每帧；例如改成 10，就是选源文件的第 0、10、20……帧。降温、熔融和退火应先按阶段切成独立轨迹，再在相同参数下比较，避免用混合温度分布解释某一温度的结构。

### 距离、周期边界与采样参数

- `cutoff=4.0` Å 是邻居搜索半径，`xmin=2.5`、`xmax=3.8` Å 是两条轴共同的统计窗口。窗口外的有效三体不会画入网格。若要保留长键，应检查它是否同时处于 cutoff 和窗口内；cutoff 应结合部分 RDF 与研究问题选择。
- `--bin-width 0.02` Å 决定统计分辨率；`--dpi 600` 决定导出图片分辨率。提高 dpi 不会增加统计信息。更细网格需要更多采样；应比较网格宽度和角窗改变后的峰位、形状与数量。
- 命令行默认使用输入的 PBC 标记。**Python 接口的 `apply_mic` 默认是 `False`**，周期体相分析要显式设置 `True`。该参数启用周期邻居搜索，实际枚举 cutoff 内的全部邻居像，并非只保留每个原子的一条最短像；小原胞中同一原子编号可以对应不同物理邻居。
- 文件必须正确携带晶胞与周期标记。普通 XYZ 通常缺少晶胞；先用 ASE 检查 `atoms.cell` 和 `atoms.pbc`，不要根据扩展名推断。有限团簇使用 `--no-pbc`。
- 轨迹应检查热平衡、采样时长、独立时间块与体系尺寸；相邻帧相关，帧数不等于独立样本数。

每次命令输出同名的 `.png`、`.npz` 和 `.json`。NPZ 保留原始网格、格边界和分析元数据；JSON 给出帧数、中心观察数、角窗内有序三体数及窗口内外计数等摘要。图片为无平滑直方图，`--log` 只改变颜色标度。

## Python 接口与结果检查

下面是与结构命令对应的脚本片段；从仓库根目录运行，或把输入路径换成自己的结构文件。

```python
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ase.io import read
from altbc_analyzer import ALTBCAnalyzer

atoms = read("example/POSCAR")
print("PBC:", atoms.pbc, "cell (Å):", atoms.cell.array)

analyzer = ALTBCAnalyzer(
    "example/POSCAR",
    center_element="Ge",
    neighbor_element="Te",
    apply_mic=True,
    cutoff=4.0,
    theta_min=155,
    theta_max=180,
    xmin=2.5,
    xmax=3.8,
    grid_size=0.02,
    histogram_mode="counts",
)
grid = analyzer.compute_grid()
print(analyzer.stats)
assert grid.sum() == analyzer.stats["in_range_triplets"]
assert np.array_equal(grid, grid.T)

fig, ax = analyzer.plot_grid(
    "outputs/python_ge_te.png", dpi=600, normalization="per_center"
)
plt.close(fig)
analyzer.save_grid("outputs/python_ge_te.npz")

with np.load("outputs/python_ge_te.npz", allow_pickle=False) as data:
    metadata = json.loads(data["metadata"].item())
    edges = data["bin_edges"]
    print(metadata)
    print("grid shape:", data["grid"].shape)
```

Python 中处理轨迹时，改为输入 `example/test.xyz`，增加 `filetype="MultiSystem", frame_interval=1`。库接口默认 `frame_interval=10`、`grid_size=0.001` Å；CLI 默认 stride 为 1、bin width 为 0.02 Å，复现实验时应显式填写。

`compute_grid()` 逐帧累积，适合较长轨迹；`compute_altbc()` 返回逐三体表，包含 `A/B/C`、`AB/BC`、`angle_ABC`、源帧编号和 A/C 相对 B 的周期像平移列，可用于核查峰对应的局域环境，但会占用更多内存。

结果首先检查以下几项：

1. `frames`、`center_observations` 是否符合输入帧和元素选择。没有目标元素、角窗内没有合格组或窗口过窄都可能产生空图。
2. 在 `counts` 模式下，网格总和是否等于 `in_range_triplets`；后者与 `out_of_range_triplets` 之和是否等于 `ordered_triplets`。窗口外占比高时，先检查被截掉的距离。
3. 原始网格是否关于对角线对称，这是双向计数约定要求的结果。对称本身不证明结构模型正确。
4. 不同相态的比较是否固定元素选择、距离窗口、角窗、网格和归一化。跨图比较颜色强度还需统一色标范围；`plot_grid` 返回 `fig, ax`，可用 Matplotlib 调整。

分析熔融—淬火—退火流程时，可将 ALTBC 与部分 RDF、配位分布、键角、结构因子及 MSD 放在一起解读。若离对角峰减弱，先区分距离趋同、角度弯折导致三体退出角窗，以及热展宽或采样差异，再讨论局域畸变变化。

## 源码与延伸阅读

- [核心统计与归一化实现](https://github.com/wangchr1617/altbc_analyzer/blob/26ae0ca0e9991340a92d0dd0b44064fba12316b8/altbc_analyzer/altbc_analyzer.py)：三体筛选、有序计数、网格及元数据输出。
- [周期邻居几何实现](https://github.com/wangchr1617/altbc_analyzer/blob/26ae0ca0e9991340a92d0dd0b44064fba12316b8/altbc_analyzer/neighbor_list.py)与[命令行参数](https://github.com/wangchr1617/altbc_analyzer/blob/26ae0ca0e9991340a92d0dd0b44064fba12316b8/altbc_analyzer/__main__.py)。
- [项目 Notebook](https://github.com/wangchr1617/altbc_analyzer/blob/26ae0ca0e9991340a92d0dd0b44064fba12316b8/example/quickstart.ipynb)：继续尝试结构和轨迹分析；使用该项目发表工作时，按仓库说明引用其指定论文。

返回[相变存储](README.md)。
