# 密度孔洞、UFF 探针势与变胞帧统计

**适用环境：Windows、macOS、Linux；已有 Multiwfn、numpy、scipy、scikit-image 和 matplotlib。**

本例用三个独立的自建模型说明不同定义：理想碳位点笼的密度孔洞、固定 Ar 对点探针的 UFF 势，以及人工构造的单 Ar 变胞帧。碳笼没有优化波函数，人工帧不是 MD 轨迹；本例不计算真实材料的孔隙率或吸附自由能。

## 输入与目录

- [cage.xyz](cage.xyz)：外接球半径 2.2 Å 的正十二面体 20 个碳位点。
- [argon.xyz](argon.xyz)：原点处一个孤立 Ar，用于 UFF 势核对。
- [frame-075.cif](frame-075.cif)、[frame-080.cif](frame-080.cif)、[frame-085.cif](frame-085.cif)：边长 7.5、8.0、8.5 Å 的周期盒子，各含一个 Ar。

将上述结构和本目录九份 `.in` 菜单复制到独立工作目录。以下命令在这个工作目录执行，`multiwfn` 应在路径中可用；菜单按 Multiwfn 2026.7.15 编写。

## 准分子密度与连通域

```bash
mkdir -p cage-density cage-density-fine domain-010 domain-050 domain-fine
cp cage.xyz cage-density/
cp cage.xyz cage-density-fine/

(cd cage-density && multiwfn cage.xyz < ../density.in > multiwfn.out)
(cd cage-density-fine && multiwfn cage.xyz < ../density-fine.in > multiwfn.out)

(cd domain-010 && multiwfn ../cage-density/density.cub < ../domain-010.in > multiwfn.out)
(cd domain-050 && multiwfn ../cage-density/density.cub < ../domain-050.in > multiwfn.out)
(cd domain-fine && multiwfn ../cage-density-fine/density.cub < ../domain-fine.in > multiwfn.out)
```

[density.in](density.in)与 [density-fine.in](density-fine.in)生成函数 `1` 的准分子密度，步距分别为 `0.20`、`0.10 Bohr`。[domain-010.in](domain-010.in)、[domain-050.in](domain-050.in)、[domain-fine.in](domain-fine.in)从已有 Cube 以不同阈值划域，导出所选域的 `domain.cub` 和 `domain.txt`。

本模型在此版本中，所需中央域的原生编号为 `1`。它与独立脚本的编号不同；更换网格或版本后，先按位置与域大小确认编号再修改菜单，不能照抄序号。后处理脚本同时检查坐标集和导出网格，选错域会直接报错。

独立脚本采用 26 邻接，将面、棱或角接触的低密度节点视为连通；这是离散网格判据。接近连通阈值时，应检查网格加密及邻接选择，不能把单个对角接触直接解释为有限尺寸探针能够穿过。

`0.010` 阈值下中央闭合域的粗、细网格体积约为 `0.38291`、`0.38424 Å³`；`0.050` 下中心已与外部连通。后者导出的二值 Cube 虽然被边界封口，仍不作为闭合孔洞体积。

## 原生 UFF 网格

```bash
mkdir -p vdw
cp argon.xyz vdw/
(cd vdw && multiwfn argon.xyz < ../vdw.in > multiwfn.out)
```

[vdw.in](vdw.in)进入 `20 → 6`，生成并分别导出 `repul.cub`、`disp.cub`、`vdW.cub`。本例要求日志中的探针为 **C**，保留实际默认设置；未更改 `settings.ini`。

本例的 UFF 原子对势以最低点距离参数化：

$$
U(r)=\epsilon_{ij}\left[\left(\frac{x_{ij}}r\right)^{12}-2\left(\frac{x_{ij}}r\right)^6\right],\qquad
x_{ij}=\sqrt{x_ix_j},\quad \epsilon_{ij}=\sqrt{\epsilon_i\epsilon_j}.
$$

因此最低点在 $r=x_{ij}$、势值为 $-\epsilon_{ij}$；$x_{ij}$ 不是标准 LJ 势的过零距离 $\sigma$，也不是单原子半径。这里使用该实现的几何混合，不直接套用其它力场的算术长度混合规则。

三份网格的函数值都是 `kcal/mol`。独立脚本按 UFF 参数和几何混合重建三个场，同时传播 Cube 坐标与数值舍入的误差界；核附近的强排斥值保留，不为作图删除。He、Ar 探针对照曲线由脚本使用明确参数计算，原生 Multiwfn 任务只使用 C 探针。

## 人工变胞帧与平滑对照

```bash
mkdir -p frame-075 frame-080 frame-085 frame-nopbc frame-gauss
for tag in 075 080 085; do
  cp "frame-$tag.cif" "frame-$tag/frame.cif"
  (cd "frame-$tag" && multiwfn frame.cif < ../free-erf.in > multiwfn.out)
done
cp frame-085.cif frame-nopbc/frame.cif
cp frame-085.cif frame-gauss/frame.cif
(cd frame-nopbc && multiwfn frame.cif < ../free-nopbc.in > multiwfn.out)
(cd frame-gauss && multiwfn frame.cif < ../free-gauss.in > multiwfn.out)
```

[free-erf.in](free-erf.in)保留周期性、默认误差函数平滑和未封口网格，请求间距 `0.25 Å`；[free-nopbc.in](free-nopbc.in)仅取消周期性；[free-gauss.in](free-gauss.in)保留周期性，改为 `FWHM=1.8R` 的 Gaussian 平滑。

三份周期帧的自由比例约为 `93.423%`、`94.495%`、`95.470%`。等帧平均与体积加权比例分别为 `94.4627%`、`94.5897%`。最后一帧取消周期性后得到 `97.6737%`，反映边界镜像漏算；仅改变平滑函数则保持原始自由体积不变。

本节按精确 CIF 晶胞体积除以不重复网格单元数确定体元，避免 Cube 步矢输出舍入带来的小幅体积漂移。统计定义及真实轨迹的采样要求见[自由空间的逐帧平均](../../../notes/计算化学/晶体自由空间、平滑网格与探针体积.md#轨迹逐帧处理与平均)。

## 提取与重绘

从仓库根目录调用脚本，它复用仓库中的正交单标量 [Cube 读取器](../../orca/minimal/weak-interactions/analyze.py)。替换为实际工作路径：

```bash
python examples/multiwfn/cavity-and-potential/analyze.py \
  --work-root /path/to/work --output-dir /path/to/work
python examples/multiwfn/cavity-and-potential/plot.py \
  --data /path/to/work/cavity-potential.json \
  --output /path/to/work/cavity-potential.png
```

[analyze.py](analyze.py)明确区分未出现中心空区、闭合内域和触及盒子边界的分量，并按坐标核对原生域。它逐点重建单 Ar 的 UFF 场与人工帧的半径球统计；限定本例模型、参数与正交网格，不作为任意分子孔洞或轨迹解析器。

[cavity-potential.json](cavity-potential.json)保存小型密度截面、阈值结果、径向势曲线、帧体积与模型定义。[plot.py](plot.py)仅凭该 JSON 即可重绘。图中密度为靠近 `z=0` 的实际网格层；径向势显示窗口截去高排斥段的可视范围，原始曲线数值仍完整保存。
