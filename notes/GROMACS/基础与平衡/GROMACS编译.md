# GROMACS 编译

**适用环境：Linux 集群。**

如果一个已有构建能在作业环境中跑通目标功能，可以先用它。需要外部 MPI、特定 SIMD 或 GPU 时，再根据目标节点准备构建。下面先用仓库的水盒验收，再保留 GROMACS 2018.8 和 FFTW 3.3.8 的旧版编译记录。旧工具链、指令集和目录应按目标机器调整。

## 一、先用一份可核对的输入验收

运行 `command -v gmx` 与 `gmx --version`，核对可执行文件路径、MPI 类型、SIMD、FFT 与 GPU 支持。外部 MPI 构建的程序名可能是 `gmx_mpi`，应检查实际运行的那个程序。然后将[水盒案例](../../../examples/gromacs/minimal/energy-minimization/README.md)的 `em.mdp`、`structure.gro` 和 `topol.top` 复制到独立目录。对使用 thread-MPI 的本机构建，可运行：

```bash
gmx grompp -f em.mdp -c structure.gro -p topol.top -o em.tpr -pp processed.top
OMP_NUM_THREADS=1 gmx mdrun -deffnm em -ntmpi 1 -ntomp 1
```

如果预处理找不到力场，先检查可执行文件对应的数据目录。如果运行时报告线程不一致，核对 `OMP_NUM_THREADS` 与 `-ntomp`。本地 GROMACS 2026.4 的 CPU 构建在 6 步后达到 `Fmax < 500`，最大力约为 383.35 kJ mol⁻¹ nm⁻¹。验收时以实际停止原因和最大力为准。

## 二、旧版构建记录中的 FFTW

下载[FFTW 压缩包](http://www.fftw.org/fftw-3.3.8.tar.gz)，上传到集群并解压，在源码目录运行：

```bash
module load gcc/9.3
./configure CC=gcc --prefix=/home/your-user/Software/fftw338 --enable-shared --enable-float --enable-sse --enable-sse2 --enable-avx --enable-avx2 --enable-avx512
```

然后 `make -j install` 开始编译。

## 三、用目标工具链构建并重复验收

下载[GROMACS 2018.8 压缩包](http://ftp.gromacs.org/pub/gromacs/gromacs-2018.8.tar.gz)，上传到集群并解压，在源码目录运行：

```bash
module load intel/2020.1.217
mkdir build
cd build
export CMAKE_PREFIX_PATH=/home/your-user/Software/fftw338
chmod u+w /home/your-user/Software/gromacs
cmake .. -DCMAKE_INSTALL_PREFIX=/home/your-user/Software/gromacs/gmx2018.8 -DGMX_MPI=ON -DGMX_SIMD=AVX2_256
make -j
make install
```

安装结束后，用新安装的可执行文件重复第一节的版本和小算例检查。CPU 单进程水盒只覆盖基本运行，若目标是 GPU 或外部 MPI，还需按实际作业方式验证相应功能。
