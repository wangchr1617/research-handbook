# 集群 3 编译 ORCA

**适用环境：Linux 集群。**

本例记录集群 3 上 ORCA 的安装过程，先准备匹配的 OpenMPI 环境，再配置 ORCA 的执行路径。

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

下载 ORCA 安装包，拖入集群并解压。设置环境变量即可：

```bash
export PATH=/home/changruiwang-ICME/Software/orca_6.1.0:$PATH
export LD_LIBRARY_PATH=/home/changruiwang-ICME/Software/orca_6.1.0:$LD_LIBRARY_PATH
```

注意执行文件路径：

```text
/home/changruiwang-ICME/Software/orca_6.1.0/orca
```
