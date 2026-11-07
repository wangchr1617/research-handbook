# OpenMX、TB2J 与 Vampire 安装

**适用环境：Linux 集群。**

从电子结构走向磁性统计模拟时，可以依次使用 OpenMX、TB2J 和 Vampire。三者承担不同任务：

- OpenMX：第一性原理电子结构计算
- TB2J：磁交换参数计算
- Vampire：原子尺度磁性模拟

## OpenMX 安装

OpenMX（Open source package for Material eXplorer）基于局域轨道 DFT，支持结构优化、分子动力学、自旋极化与非共线磁性，也可将结果交给 TB2J 等工具分析。下面保留 OpenMX 3.9 的集群安装步骤；精简命令版见[编译笔记](OpenMX编译.md)。

### 下载

从[OpenMX 官网](https://www.openmx-square.org/download.html)下载 OpenMX 3.9 源码与对应补丁 patch3.9.9。下面的节点名和 Intel 模块对应原集群环境：

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

TB2J 是计算磁交换参数的 Python 包，可以处理 Wannier90、SIESTA、OpenMX 和 ABACUS 等软件的输出。接口与使用方式见[官方文档](https://tb2j.readthedocs.io/en/latest/)。

集群联网后执行 `pip install TB2J-OpenMX`。

## Vampire 安装

Vampire 是一个原子尺度的磁性模拟软件，支持：

- 自旋动力学模拟
- 蒙特卡洛模拟
- 退磁场计算
- 热辅助记录模拟
- GPU 加速（5.0+ 版本）

程序与资料见[Vampire 官网](https://vampire.york.ac.uk/)。以下保留作者使用 Vampire 4.0 的安装记录，该版本在作者的使用中运行较稳定。

```bash
tar xvf vampire-4.0-linux.tar.gz
```

解压后生成可执行文件 `./linux/vampire`。

需要并行功能时，可按所用版本的说明选择相应构建。
