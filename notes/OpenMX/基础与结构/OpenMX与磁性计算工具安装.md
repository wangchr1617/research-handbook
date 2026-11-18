# OpenMX、TB2J 与 Vampire 安装

**适用环境：Linux 集群。**

如果只想比较 bcc Fe 的铁磁和反铁磁能量，OpenMX 就够了。若要用原子自旋模型研究热涨落或磁化动力学，还需要从电子结构提取交换参数，再把模型交给自旋模拟程序。先根据研究问题决定做到哪一步，再准备对应工具。

## 一、先用 OpenMX 得到目标磁态

已有 OpenMX 时，先用[磁序对照案例](../电子结构与磁性/OpenMX磁序与局域磁矩.md)核对数据库和最终局域磁矩；需要从源码复现旧环境时，按 [OpenMX 3.9 编译笔记](OpenMX编译.md)配好补丁、MPI 和 MKL。后续要用 TB2J 时，另检查接口是否支持所用 OpenMX 版本及输出格式。

案例中两个分支的能量差可以比较固定构型下的磁序。若要继续提取交换参数，则先选择自洽后仍处于预期磁序的参考态，并在 OpenMX 输入里开启 `HS.fileout on`。保留同一次计算的 `<前缀>.scfout` 和 `<前缀>.xyz`，前者包含哈密顿量与重叠矩阵，后者提供结构。用 `System.Name` 核对文件前缀。[TB2J 的 OpenMX 接口说明](https://tb2j.readthedocs.io/en/stable/src/openmx.html)

## 二、用 TB2J 从电子结构得到交换参数

在已激活的 Python 环境安装 OpenMX 接口，并确认命令可用：

```bash
python -m pip install TB2J-OpenMX
openmx2J.py --help
```

实际运行时，按接口提示指定 OpenMX 输出目录、前缀、磁性元素和 k 网格。先核对程序读到的原子和输出中的交换对，再检查不同 k 网格和交换距离范围下的结果。命令能启动只说明环境可用，参数是否足够稳定要靠上述对照判断。[TB2J 官方教程](https://tb2j.readthedocs.io/en/latest/src/tutorial.html)

## 三、把交换模型交给 Vampire

如果研究目标是有限温度下的磁化或自旋演化，再准备 Vampire。以下是原集群使用的 4.0 二进制包解压命令，路径对应这份发行包：

```bash
tar xvf vampire-4.0-linux.tar.gz
```

解压后的入口为 `./linux/vampire`。使用其它版本或并行构建时，按对应版本的安装说明查入口及依赖。[Vampire 官网](https://vampire.york.ac.uk/)

接入之前，逐项核对交换能单位、铁磁和反铁磁的符号、磁矩或单位自旋的归一化，以及原子对是否重复计数。可先选一对自旋，用两边的模型约定分别算平行与反平行的能差，再检查导入后能否得到同一能差。仓库的 bcc Fe 案例用于验收 DFT 磁态，这里的交换参数交接需要另外生成并验证输入。
