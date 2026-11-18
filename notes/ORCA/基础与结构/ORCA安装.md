# 集群 3 安装 ORCA 与 OpenMPI

**适用环境：Linux 集群。**

ORCA 驱动能找到，并不代表它已能在作业中启动并行模块。验收可以分两步：先用一个进程跑通水分子单点，再用同一个输入验证目标 MPI 配置。下文保留集群 3 上 ORCA 6.1.0 与 OpenMPI 4.1.8 的安装记录。实际版本应以下载包的配套说明和目标节点为准。

## 一、先验收串行，再核对并行

将[单点案例](../../../examples/orca/minimal/single-point/README.md)的 `orca.inp` 和 `structure.xyz` 复制到独立目录。将下面的驱动路径换成自己的绝对路径：

```bash
/path/to/orca orca.inp > orca.out 2>&1
```

保留输入中的单进程设置，检查日志是否正常结束、写出了 GBW，并得到约 −76.27350518 Hartree。串行验证通过后，可在另一个独立目录把 `%pal nprocs 1 end` 改成作业允许的进程数，用完整路径启动 ORCA 驱动，由它调用并行模块。若仅在并行时报错，先检查作业环境中解析到的 `mpiexec` 和 MPI 库是否与 ORCA 安装包兼容。参见 [ORCA 并行运行说明](https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/parallel.html)。

## 二、准备旧版案例所用的 OpenMPI

加载编译环境：

```bash
module load gcc/9.3
```

下载 OpenMPI 安装包，拖入集群并解压。进入 `openmpi-4.1.8` 目录并执行下列命令编译：

```bash
./configure --prefix=/home/your-user/Software/openmpi-4.1.8 --disable-builtin-atomics --disable-oshmem
make all
make install
```

设置环境变量：

```bash
export PATH=/home/your-user/Software/openmpi-4.1.8/bin:$PATH
export LD_LIBRARY_PATH=/home/your-user/Software/openmpi-4.1.8/lib:$LD_LIBRARY_PATH
```

检查 OpenMPI 是否编译成功：

```text
mpiexec -V
```

## 三、安装 ORCA 后用实际作业环境验收

加载编译环境：

```bash
module load gcc/9.3
export PATH=/home/your-user/Software/openmpi-4.1.8/bin:$PATH
export LD_LIBRARY_PATH=/home/your-user/Software/openmpi-4.1.8/lib:$LD_LIBRARY_PATH
```

将 ORCA 安装包上传到集群并解压，再把程序目录加入环境变量：

```bash
export PATH=/home/your-user/Software/orca_6.1.0:$PATH
export LD_LIBRARY_PATH=/home/your-user/Software/orca_6.1.0:$LD_LIBRARY_PATH
```

本例 ORCA 驱动的完整路径为：

```text
/home/your-user/Software/orca_6.1.0/orca
```
