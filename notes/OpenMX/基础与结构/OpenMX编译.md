# OpenMX 编译

**适用环境：Linux 集群。**

下面记录 OpenMX 3.9 与 patch3.9.9 在 Intel 2020 环境下的编译步骤。路径和编译器配置对应这一环境，使用时按实际安装位置调整。

先下载并解压源码与补丁：

```bash
wget https://www.openmx-square.org/openmx3.9.tar.gz
tar -xvf openmx3.9.tar.gz
cd openmx3.9/source
wget https://www.openmx-square.org/bugfixed/21Oct17/patch3.9.9.tar.gz
tar -xvf patch3.9.9.tar.gz
mv kpoint.in ../work/
```

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
