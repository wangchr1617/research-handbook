# NEP-LAMMPS 编译

**适用环境：Linux 集群。**

下面记录在原集群中编译 NEP_CPU 接口的步骤。软件目录沿用原示例，使用时替换为自己的路径；另一组编译记录见[GPUMD 编译指南](GPUMD编译.md#编译带-nep-插件的-lammps)。

先用 `ssh cu02` 进入编译节点，再加载 Intel 模块：

```bash
module load intel/2020.1.217
```

下载 LAMMPS 并解压，重命名为 `lammps-nep`：

```bash
git clone --depth=1 https://github.com/lammps/lammps
unzip lammps-release.zip
mv lammps-release lammps-nep
```

然后安装 NEP_CPU：

```bash
git clone https://github.com/brucefan1983/NEP_CPU.git
unzip NEP_CPU-main.zip
cd NEP_CPU-main/
cp src/* interface/lammps/USER-NEP/
cp interface/lammps/USER-NEP/ ../lammps-nep/src/
```

最后编译 LAMMPS：

```bash
cd ~/soft/lammps-nep/
mkdir build
cd build/
/home/yidongli-ICME/soft/cmake/bin/cmake ../cmake \
  -DCMAKE_BUILD_TYPE=Release \
  -DPKG_NEP=ON
make -j$(nproc) VERBOSE=1
make install
```

验证 LAMMPS 安装：`$HOME/soft/lammps-nep/build/lmp -help`

编译完成后使用 `logout` 退回登录节点。
