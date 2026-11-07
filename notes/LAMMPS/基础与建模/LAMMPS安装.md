# LAMMPS 安装

**适用环境：Linux 集群。**

本文保留原集群中 LAMMPS 29Sep2021、23Jun2022 等版本的构建记录。目录、编译器和扩展接口对应原环境；使用其他版本时，先核对其构建要求。

## LAMMPS make 安装

先准备 LAMMPS 源码、MPI 与 FFTW。原集群的 MPI 随 Intel 编译环境提供，可用 `which mpirun` 核对路径；FFTW 位于 `/opt/software/`。源码从[LAMMPS 官方下载页](https://www.lammps.org/download.html)获取。

1.  解压 LAMMPS 安装包：`tar -xzvf lammps-stable.tar.gz`；
2.  进入 LAMMPS 安装目录，并修改配置文件：

```bash
cd /home/zfli-ICME/software/lammps/lammps-29Sep2021/
vim src/MAKE/OPTIONS/Makefile.g++_mpich                # 修改该文件
    MPI_INC =       -DMPICH_SKIP_MPICXX -DOMPI_SKIP_MPICXX=1
    MPI_PATH =  -L/opt/intel2020/intelpython3/bin/mpirun
    MPI_LIB =

    FFT_INC = -I/opt/software/fftw3.3.4/include
    FFT_PATH = -L/opt/software/fftw3.3.4/lib
    FFT_LIB =
```

3.  连接编译节点：`ssh cu02`；
4.  加载 Intel 编译环境：`module load intel/2020.1.217`；
5.  依次输入以下命令：

```bash
make yes-molecule
make yes-kspace
make yes-rigid
make yes-manybody
make g++_mpich
```

编译完成后 `src` 目录下会生成名为 `lmp_g++_mpich` 的可执行文件。

> 使用命令 `make package-installed` 查看编译了哪些包。

### LAMMPS-MLIP-interface 安装

安装 MTP 势函数的接口。

首先需要访问 [网址](https://gitlab.com/ashapeev/mlip-2) 下载 mlip 安装包。
本例只编译 LAMMPS 接口所需的 **libinterface** 库：

```bash
ssh cu02
module load intel/2020.1.217
cd mlip-2
mkdir build
cd build
cmake ..
make libinterface
```

编译完成后，该目录下会出现 `lib_mlip_interface.a` 文件，将其复制到 `interface-lammps-mlip-2-master` 目录下。

然后开始编译 MTP 势函数的接口。
先在 `preinstall.sh` 脚本末尾添加以下命令，在编译时将这些包也编译好：

```bash
make yes-molecule
make yes-kspace
make yes-rigid
make yes-manybody
make yes-REPLICA        # neb计算用
```

原环境使用 `g++_mpich` 目标构建这一接口时曾报错，因此下面采用 `intel_cpu_intelmpi`：

```bash
module load intel/2020.1.217
./install.sh ../lammps-23Jun2022 intel_cpu_intelmpi
```

编译完成后该目录下会包含名为 `lmp_intel_cpu_intelmpi` 的可执行文件。

## LAMMPS CMake 安装

> CMake 和 make 安装方式不能混用，如果用 CMake 安装 LAMMPS，后续安装扩展包时不能用 make 安装。

### 检查并准备安装环境

首先检查 CMake，至少需要 3.10 及以上版本。

```bash
which cmake
cmake --version
```

CMake 构建分为三个阶段：

1. 配置（configuration）：确定编译器、依赖库和启用的功能。
2. 编译（compilation）：构建库与可执行程序。
3. 安装（installation）：将构建产物复制到指定安装位置。

配置和编译必须在单独的 build 目录中，并且该目录必须不同于源目录。

此外，源目录 `src` 必须保持原始状态，因此在此之前不能用 make 方式进行编译，因为 make 是在源目录中进行的。
可以用 `make no-all purge` 删除 `make` 创建的源文件。

建议在 LAMMPS 顶层目录下创建独立的构建目录，例如并行版用 `build-parallel`，串行版用 `build-serial`。
这样在一次编译过程中所有的辅助文件都在该目录下。

### 安装

进入 build 目录，然后运行 `cmake ../cmake` 命令，屏幕上会输出配置进度，后面包括启用的特性，选项和编译器设置。

```bash
tar -xzvf lammps-stable.tar.gz

cd lammps-23Jun2022
mkdir build && cd build
cmake ../cmake                      # 这一步并不会编译代码

# 这两种方式任选一种都可以编译，一定是在build目录下，make方式还需要make install
cmake --build .                     # 这一步才开始编译

make -j 8
make install
```

配置时留意 **Could NOT find** 等信息，区分可选功能与当前任务必需的库；缺少必需依赖时，先补齐再编译。

### 设置选项

编译时可以用 `-D` 选项启用、关闭或调整设置，格式为 `-D VARIABLE=VALUE`。`VALUE` 一般为布尔值（on/off、yes/no、1/0）或字符串；字符串中若有空格，需要用双引号括起来。

设置选项可以分为两类：

- CMake 自带的设置选项
- LAMMPS 指定的设置选项

如果要编译 LAMMPS 的一些扩展包，设置方式为 `-D PKG_<NAME>=on`；如果要禁用某个扩展包：`-D PKG_<NAME>=no`。name 即为扩展包的名称。

#### presets 设置

当安装的扩展包很多的时候，都写在命令行中会很臃肿，且容易出错。可以通过设置 preset 文件，将需要启用的设置放到源目录的 `cmake/presets` 文件夹中，在命令行中指定该文件即可。preset 文件通过 `-C` 加载。

```bash
cmake -C ../cmake/presets/basic.cmake -D PKG_MISC=on ../cmake
cmake -C ../cmake/presets/clang.cmake -C ../cmake/presets/most.cmake ../cmake
cmake -C ../cmake/presets/basic.cmake -D BUILD_MPI=off ../cmake
```

#### 扩展包安装

##### VORONOI package

设置 `DOWNLOAD_VORO=yes` 时，程序会尝试下载依赖。在无法联网的环境中，可以根据提示中的链接手动下载，将压缩包复制到构建目录下的 `build-common/voro_build-prefix/src/voro++-0.4.6.tar.gz`，然后继续编译。

```bash
cmake -C ../cmake/presets/basic.cmake -D PKG_VORONOI=yes -D DOWNLOAD_VORO=yes ../cmake
cmake -C ../cmake/presets/basic.cmake -D PKG_VORONOI=yes -D DOWNLOAD_VORO=yes -D PKG_REPLICA=yes -D PKG_ML-SNAP=yes ../cmake
```

##### PYTHON package

要想将 LAMMPS 与 Python 连接起来，需要将 LAMMPS 通过共享库的方式编译（`BUILD_SHARED_LIBS`），而不是静态链接库。编译完之后会有 `liblammps.so` 动态链接库。

- `Python_EXECUTABLE`：Python 解释器位置
- `PKG_PYTHON`：是否安装 Python 包
- `BUILD_SHARED_LIBS`：以共享连接库的方式安装

> 注：在和 `VORONOI` 扩展包一起编译时，`VORONOI` 默认会把生成的动态链接库删除，这时候需要进入 `voro_build-prefix/src/` 目录将压缩包解压，然后将 `voro_build-prefix/src/voro++-0.4.6/Makefile` 中最后删除动态链接库的命令注释掉即可。

```bash
cmake -C ../cmake/presets/basic.cmake -D PKG_VORONOI=yes -D DOWNLOAD_VORO=yes -D PKG_REPLICA=yes -D PKG_ML-SNAP=yes -D PKG_PYTHON=yes -D Python_EXECUTABLE=/home/zfli-ICME/software/anaconda3/bin/python3.8 -D BUILD_SHARED_LIBS=yes ../cmake
cmake --build .

# 编译完成后需要再build目录下设置，有以下方式
# 第一种，但是这种方式需要联网好像
make install-python

# 第二种，直接配置，in place use。PYTHONPATH指向根目录下的python目录；LD_LIBRARY_PATH指向build目录，是为了找到动态链接库
# 采用这种方式的话，在编译时最好不要用`LAMMPS_MACHINE=name`选项，因为产生的`liblammps_mpi.so`动态链接库不会被解析，原始的python目录没有指定name
# 将下面的两行添加到.bashrc文件，注意添加到conda初始化命令后面
export PYTHONPATH=/home/zfli-ICME/software/lammps-23Jun2022/python:${PYTHONPATH}    # 或者 /home/zfli-ICME/software/lammps-23Jun2022/build-python-1/python/lib
export LD_LIBRARY_PATH=/home/zfli-ICME/software/lammps-23Jun2022/build-python-1:${LD_LIBRARY_PATH}
```

## GPU 版本 LAMMPS CMake 安装

```bash
ssh gpu01

# 需要自己将cmake路径添加到PATH环境变量中
export PATH=/opt/software/cmake-3.15.1/bin/:$PATH

mkdir build-gpu
cmake -C ../cmake/presets/basic.cmake -D PKG_GPU=on -D GPU_API=cuda -D GPU_PREC=mixed -D GPU_ARCH=sm_86 -D CUDPP_OPT=yes ../cmake

make -j 8
make install            # 完成后会在该目录下生成一个lmp可执行文件，可以随意命名

# 调用gpu版本的lammps做计算，需要加 -sf -pk 两个参数。-sf指在所有支持gpu加速的脚本命令前加上gpu前缀；-pk gpu后跟的是节点数，几块gpu就填几
mpirun -np 8 lmp_gpu -sf gpu -pk gpu 1 -in in.file
```

```bash
cmake -C ../cmake/presets/kokkos-cuda.cmake -C ../cmake/presets/basic.cmake -D PKG_GPU=on -D GPU_API=cuda -D GPU_PREC=mixed -D GPU_ARCH=sm_86 -D CUDPP_OPT=yes -D PKG_ML-SNAP=yes ../cmake
```
