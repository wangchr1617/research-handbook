# 集群 3 安装 ORCA 与 OpenMPI

**适用环境：Linux 集群。**

本例记录集群 3 上 ORCA 6.1.0 的安装过程：先编译 OpenMPI 4.1.8，再解压 ORCA 安装包并配置执行路径。下面的模块名与个人目录对应原环境，使用时按实际位置替换。

## 编译 OpenMPI

加载编译环境：

```bash
module load gcc/9.3
```

下载 OpenMPI 安装包，拖入集群并解压。进入 `openmpi-4.1.8` 目录并执行下列命令编译：

```bash
./configure --prefix=/home/changruiwang-ICME/Software/openmpi-4.1.8 --disable-builtin-atomics --disable-oshmem
make all
make install
```

设置环境变量：

```bash
export PATH=/home/changruiwang-ICME/Software/openmpi-4.1.8/bin:$PATH
export LD_LIBRARY_PATH=/home/changruiwang-ICME/Software/openmpi-4.1.8/lib:$LD_LIBRARY_PATH
```

检查 OpenMPI 是否编译成功：

```text
mpiexec -V
```

## 安装 ORCA

加载编译环境：

```bash
module load gcc/9.3
export PATH=/home/changruiwang-ICME/Software/openmpi-4.1.8/bin:$PATH
export LD_LIBRARY_PATH=/home/changruiwang-ICME/Software/openmpi-4.1.8/lib:$LD_LIBRARY_PATH
```

将 ORCA 安装包上传到集群并解压，再把程序目录加入环境变量：

```bash
export PATH=/home/changruiwang-ICME/Software/orca_6.1.0:$PATH
export LD_LIBRARY_PATH=/home/changruiwang-ICME/Software/orca_6.1.0:$LD_LIBRARY_PATH
```

本例 ORCA 驱动的完整路径为：

```text
/home/changruiwang-ICME/Software/orca_6.1.0/orca
```
