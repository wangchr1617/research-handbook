# LAMMPS 计算声子谱

**适用环境：Linux（LAMMPS 与 Phonopy）。**

力常数算出来以后，若拿另一份晶胞去画声子谱，曲线仍可能生成，分支和高对称点却失去对应。这个流程要让 LAMMPS 的结构与 NEP 类型映射、Phonopy 读取的参考结构和声子路径都指向同一个 GeTe 晶相。先沿文件逐个检查，再跑有限位移。

## 一、先验证 Python 能实际调用 LAMMPS

首先 `pip install phonolammps` 安装 phonolammps。
然后安装 LAMMPS 的 Python 接口，依次运行：

```bash
make serial mode=shlib
make install-python
```

上述 make 命令属于原构建环境。导入 Python 模块后，还应初始化 LAMMPS 实例并用目标势检查一次受力，确认模块找到的是包含 NEP 接口的共享库。

## 二、把结构、元素映射和位移超胞对齐

准备 `in.lammps`，使读取的结构、NEP 模型和后面 `POSCAR` 描述同一体系。下方 `gete.data` 是占位文件名，使用时换成自己的 GeTe 输入。先核对原子数、元素类型、晶胞、坐标顺序以及 NEP 文件的类型映射。

```text
units    metal
atom_style  atomic
dimension 3
boundary p p p
read_data     gete.data #读取结构
pair_style    nep nep.txt  #选择自己的势函数
pair_coeff    * *
```

利用 phonolammps 生成二阶力矩阵：

```text
phonolammps in.lammps -c POSCAR --dim 4 4 4
```

运行完之后会生成二阶力常数矩阵 `FORCE_CONSTANTS`。

## 三、按同一晶相的路径绘图并核对单位

然后利用 `vaspkit 305 3` 生成高对称点路径文件 `KPATH.in` 并重命名为 `band.conf`。
下面是原路径记录，仅在原胞定义和晶相一致时使用。若换相、变换原胞或改变倒格基矢，应从实际结构重新生成路径。

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

绘图前检查 `band.dat` 的高对称点坐标，并把纵轴单位与 Phonopy 输出对上。若改用 THz，就不要沿用写成 cm⁻¹ 的轴标签。低频异常时，可按[有限位移方法](../../VASP/振动与热力学/VASP声子谱计算.md)复查结构残余受力、位移量和超胞收敛。
访问 [网址](https://henriquemiranda.github.io/phononwebsite/phonon.html) 并上传 `band.yaml` 可以查看声子谱的振动模式。
