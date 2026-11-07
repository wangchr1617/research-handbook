# QE 编译

**适用环境：Linux 集群。**

## 集群 3 编译 QE 7.3.1

下面保留集群 3 的 QE 7.3.1 编译记录，编译器版本、路径和节点名对应当时环境；在其他集群使用时需相应替换。先用 `ssh cu02` 进入编译节点，再加载编译环境：

```bash
module load intel/2020.1.217
module load gcc/9.3
```

执行以下命令查看编译环境是否加载成功：

```bash
icc --version
icpc --version
ifort --version
mpirun --version
echo $MKLROOT
```

核对编译器、MPI 版本与 MKL 路径，原环境的输出示例如下：

<div align="left">
<img alt="QE 编译示例图" src="assets/编译-001.png" width="50%" />
</div>

访问 [QE 官网](https://www.quantum-espresso.org/) 下载 QE 安装包，以 `qe-7.3.1-ReleasePack.tgz` 为例。
依次执行以下命令：

```bash
tar -zvxf qe-7.3.1-ReleasePack.tar.gz
cd qe-7.3.1/
./configure --with-cuda=no --with-scalapack=intel --with-scalapack-qrcp=yes MPIF90=mpiifort FC=ifort FCFLAGS=-O3 CC=mpiicc CFLAGS=-O3
vi make.inc
make all -j
make epw
```

注意修改 `make.inc` 对应字段为以下内容：

```bash
FFLAGS = -O3 -assume byterecl -g -traceback
BLAS_LIBS = -L${MKLROOT}/lib/intel64 -lmkl_scalapack_lp64 -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lmkl_blacs_intelmpi_lp64 -lpthread -lm -ldl
LAPACK_LIBS = -L${MKLROOT}/lib/intel64 -lmkl_scalapack_lp64 -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lmkl_blacs_intelmpi_lp64 -lpthread -lm -ldl
SCALAPACK_LIBS = -L${MKLROOT}/lib/intel64 -lmkl_scalapack_lp64 -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lmkl_blacs_intelmpi_lp64 -lpthread -lm -ldl
FFT_LIBS = -L${MKLROOT}/lib/intel64 -lmkl_scalapack_lp64 -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lmkl_blacs_intelmpi_lp64 -lpthread -lm -ldl
MPI_LIBS = -L/opt/intel2020/impi/2019.7.217/intel64/lib
```

编译完成后，检查 `qe-7.3.1/bin` 中是否生成所需的 `.x` 可执行程序。完成操作后，用 `logout` 退出编译节点。

## QE 提交脚本

下面给出 QE 在集群 3 适用的 PBS 提交脚本：

```bash
#PBS -N qe
#PBS -l nodes=1:ppn=24
#PBS -l walltime=600:00:00
#PBS -q batch
#PBS -V
#PBS -S /bin/bash

export MODULEPATH=/opt/modulefiles
module load intel/2020.1.217
module load gcc/9.3

NP=`cat $PBS_NODEFILE | wc -l`
NN=`cat $PBS_NODEFILE | sort | uniq | tee /tmp/nodes.$$ | wc -l`

cat $PBS_NODEFILE > /tmp/nodefile.$$
cd $PBS_O_WORKDIR
ulimit -s unlimited

EXEC=/home/changruiwang-ICME/Software/qe-7.3.1/bin/pw.x
mpirun -machinefile $PBS_NODEFILE -np $NP $EXEC -pd .true. < pw.inp > output
```

## 赝势下载

[QE 官网](https://www.quantum-espresso.org/pseudopotentials/) 给出了 SSSP 赝势的下载链接，赝势文件可以直接下载。
以 `SSSP_1.3.0_PBE_efficiency.tar.gz` 为例，下载后上传到集群，解压到统一的赝势目录，并在输入中指定该路径。
