# LAMMPS 计算声子谱

**适用环境：Linux（LAMMPS 与 Phonopy）。**

本流程由 LAMMPS 提供受力，phonolammps 组织有限位移，再用 Phonopy 处理力常数与声子路径。下面保留 GeTe 示例的输入与后处理命令。

## 安装环境

首先 `pip install phonolammps` 安装 phonolammps。
然后安装 LAMMPS 的 Python 接口，依次运行：

```bash
make serial mode=shlib
make install-python
```

在 Python 能 `from lammps import lammps` 导入即可。

## 使用 NEP 势函数计算 GeTe 声子谱

准备 `in.lammps`，使读取的结构、NEP 模型和后面 `POSCAR` 描述同一体系。下面的 `graphene.data` 是示例文件名，应用到 GeTe 时替换为对应结构文件：

```text
units    metal
atom_style  atomic
dimension 3
boundary p p p
read_data     graphene.data #读取结构
pair_style    nep nep.txt  #选择自己的势函数
pair_coeff    * *
```

利用 phonolammps 生成二阶力矩阵：

```text
phonolammps in.lammps -c POSCAR --dim 4 4 4
```

运行完之后会生成二阶力常数矩阵 `FORCE_CONSTANTS`。

然后利用 `vaspkit 305 3` 生成高对称点路径文件 `KPATH.in` 并重命名为 `band.conf`。
修改 `band.conf` 如下所示：

```text
ATOM_NAME = Ge Te # 元素名称
NPOINTS = 501
DIM = 4 4 4 # 扩胞指数
BAND = 0.000000 0.000000 0.000000 0.500000 0.500000 0.500000 0.759157 0.240843 0.500000, 0.500000 -0.240843 0.240843 0.500000 0.000000 0.000000 0.000000 0.000000 0.000000 0.370421 -0.370421 0.000000, 0.629579 0.000000 0.370421 0.500000 0.000000 0.500000 0.000000 0.000000 0.000000
BAND_LABELS = $\Gamma$ T H$_2$ H$_0$ L $\Gamma$ S$_0$ S$_2$ F $\Gamma$

MP = 30 30 30
TETRAHEDRON = .TRUE.
PDOS = 1, 2
BAND_CONNECTION = .TRUE.
EIGENVECTORS = .TRUE. # 输出本征矢
FORCE_CONSTANTS = READ # 读取 FORCE_CONSTANTS

# FORCE_SETS = READ # 也可以选择读取 FORCE_SETS
# IRREPS = 0  0  0
# SHOW_IRREPS = .TRUE.
# LITTLE_COGROUP = .TRUE.
```

依次运行下面命令输出 `band.yaml`、`band.dat` 和 `band_dos.pdf`：

```bash
phonopy --dim="4 4 4" -c POSCAR --factor=521.471 -p -s band.conf
phonopy-bandplot --gnuplot band.yaml > band.dat
```

`--factor=521.471` 是这组旧流程从力常数和质量单位得到波数的换算因子，并非 THz 到 $cm^{-1}$ 的换算倍数；1 THz 约为 33.3564 cm⁻¹。新版 Phonopy 的接口与换算选项已有变化，使用时核对[官方单位说明](https://phonopy.github.io/phonopy/setting-tags.html#frequency-conversion-factor)，热学计算应保留其要求的 THz 频率约定。

`band.dat` 可以直接拖进 Origin 画图，第 2 行是 band.conf 中高对称点对应的横坐标。
访问 [网址](https://henriquemiranda.github.io/phononwebsite/phonon.html) 并上传 `band.yaml` 可以查看声子谱的振动模式。
