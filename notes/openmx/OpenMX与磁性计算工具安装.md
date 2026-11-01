# OpenMX、TB2J 与 Vampire 安装

**适用环境：Linux 集群。**

本教程介绍了一套完整的磁性材料计算工具链（OpenMX、TB2J 和 Vampire）的安装过程，包括：

- OpenMX：第一性原理电子结构计算
- TB2J：磁交换参数计算
- Vampire：原子尺度磁性模拟

## OpenMX 安装

OpenMX（Open source package for Material eXplorer）是一款开源的第一性原理计算软件包，具有以下特点：

- 基于局域轨道基组的密度泛函理论实现
- 支持结构优化和分子动力学
- 支持自旋极化计算和非共线磁矩
- 高效并行计算
- 可与 TB2J 等磁性计算软件对接

### 下载

访问 OpenMX 官网：https://www.openmx-square.org/download.html

下载 OpenMX 3.9 版本的源代码包

下载对应的补丁文件 patch3.9.9

```bash
ssh cu02                                    # 登录计算节点
module load intel/2020.1.217                # 加载Intel编译环境
```

### 解压

```bash
tar xvf openmx3.9.tar.gz                    # 登录计算节点
cp patch3.9.9.tar.gz openmx3.9/source/      # 复制补丁到源码目录
cd openmx3.9/source/                        # 进入源码目录
tar xvf patch3.9.9.tar.gz                   # 解压补丁
mv kpoint.in ../work/                       # 移动k点文件到工作目录
```

### 修改 makefile

```makefile
vim makefile
# 修改以下配置项:
# MKLROOT: 指定MKL库路径
# CC: C编译器配置，启用OpenMP和MKL优化
# FC: Fortran编译器配置
# LIB: 链接库配置
MKLROOT = /opt/intel2020/compilers_and_libraries_2020.1.217/linux/mkl
CC = mpiicc -O3 -xHOST -ip -no-prec-div -qopenmp -I${MKLROOT}/include -I${MKLROOT}/include/fftw
FC = mpiifort -O3 -xHOST -ip -no-prec-div -qopenmp
LIB= -L${MKLROOT}/lib/intel64 -lmkl_scalapack_lp64 -lmkl_intel_lp64 -lmkl_intel_thread -lmkl_core -lifcore -lmkl_blacs_intelmpi_lp64 -liomp5 -lpthread -lm -ldl
```

### 编译

```bash
make clean
make all
make install
```

编译完成后，生成可执行文件 `openmx3.9/work/openmx`。

## TB2J 安装

TB2J 是一个用于计算磁交换参数的 Python 包，支持多种第一性原理计算软件输出：

- Wannier90
- SIESTA
- OpenMX
- ABACUS

官网：https://tb2j.readthedocs.io/en/latest/

集群联网后执行 `pip install TB2J-OpenMX`。

## Vampire 安装

Vampire 是一个原子尺度的磁性模拟软件，支持：

- 自旋动力学模拟
- 蒙特卡洛模拟
- 退磁场计算
- 热辅助记录模拟
- GPU 加速（5.0+ 版本）

官网：https://vampire.york.ac.uk/

我使用的是 Vampire 4.0，运行比较稳定。

```bash
tar xvf vampire-4.0-linux.tar.gz
```

解压后生成可执行文件 `./linux/vampire`。

Vampire 新版本添加了并行计算功能，可以按需要尝试。
