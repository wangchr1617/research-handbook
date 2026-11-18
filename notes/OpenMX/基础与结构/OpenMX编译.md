# OpenMX 编译

**适用环境：Linux 集群。**

需要复现 OpenMX 3.9 的计算环境时，可按这套 Intel 2020 工具链编译。源码、补丁、MPI 编译器和 MKL 链接库是一组需要配套的条件。路径按实际安装位置调整。

## 一、准备 3.9 源码与对应补丁

在可写的构建目录下载、解包：

```bash
wget https://www.openmx-square.org/openmx3.9.tar.gz
tar -xvf openmx3.9.tar.gz
cd openmx3.9/source
wget https://www.openmx-square.org/bugfixed/21Oct17/patch3.9.9.tar.gz
tar -xvf patch3.9.9.tar.gz
mv kpoint.in ../work/
```

## 二、用同一套 Intel MPI 与 MKL 编译

在 `openmx3.9/source/makefile` 中找到 MKL 路径、编译器和链接库配置，修改为：

```makefile
MKLROOT = /opt/intel2020/compilers_and_libraries_2020.1.217/linux/mkl
CC = mpiicc -O3 -xHOST -ip -no-prec-div -qopenmp -I${MKLROOT}/include -I${MKLROOT}/include/fftw
FC = mpiifort -O3 -xHOST -ip -no-prec-div -qopenmp
LIB= -L${MKLROOT}/lib/intel64 -lmkl_scalapack_lp64 -lmkl_intel_lp64 -lmkl_intel_thread -lmkl_core -lifcore -lmkl_blacs_intelmpi_lp64 -liomp5 -lpthread -lm -ldl
```

开始编译：

```bash
module load intel/2020.1.217
make clean
make all -j 4
make install
```

## 三、用 H₂ 单点验收二进制和数据库

`make install` 完成后，在源码树的 `work/` 目录确认生成了 `openmx`。复制[仓库 H₂ 案例](../../../examples/openmx/minimal/single-point/README.md)到独立目录，在有可用计算资源的环境执行：

```bash
OPENMX_EXEC=/path/to/openmx3.9/work/openmx \
OPENMX_DATA=/path/to/DFT_DATA19 python3 run.py
```

`run.py` 用指定的二进制启动单线程任务，将启动日志写到 `openmx.out`。先确认 MPI 和动态库能加载，再看 `system.out` 是否记录了 SCF 和总能。若程序已启动却找不到基组或势，检查 `OPENMX_DATA` 下的 `PAO/`、`VPS/` 和输入使用的物种名。结果读取及残差检查见[单点能与受力](OpenMX单点能与受力.md)。

编译和安装位置可对照 [OpenMX 3.9 官方安装示例](https://www.openmx-square.org/Installation_OpenMX_WSL_EN.pdf)。
