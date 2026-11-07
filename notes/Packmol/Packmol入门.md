# Packmol 入门

**适用环境：Linux（编译与命令示例）。**

Packmol 用已有结构模板装填指定空间，生成后续模拟所需的初始坐标。下面以 GeTe 为例介绍输入与运行方式；装填后的结构还需要经过相应的最小化和平衡。

## 安装与运行

从[官网](https://m3g.github.io/packmol/download.shtml)下载 `packmol.tar.gz`，上传到集群并解压。在源码目录执行 `./configure`，再用 `make` 编译，生成可执行文件 `packmol`。

将安装目录加入 `~/.bashrc` 中的 `PATH`。下面是原示例的路径，使用时替换为自己的安装位置：

```bash
export PATH=/home/changruiwang-ICME/Software/packmol-20.14.2:${PATH}
```

使修改后的 `PATH` 生效后，输入 `packmol`，检查程序是否能启动。

将 `.inp` 文件重定向到 `packmol` 即可运行程序，例如：

```bash
packmol < test.inp
```

## 用 GeTe 模板生成初始结构

需要准备两个文件：结构模板指定“放什么”，输入文件指定“放多少、放在哪里”。本例为液相 GeTe 模拟准备初态，结构模板 `model.xyz` 如下：

```text
2
Lattice="-2.92042768e-08 2.9909695976823745 2.99096938925063 2.990969671591604 -9.98001108e-08 2.990969459364865 2.9909696608638106 2.99096965747627 -8.91261311e-08" Properties=species:S:1:pos:R:3 pbc="T T T"
Ge      -0.00000000       0.00000000       0.00000000
Te       2.99096965       2.99096958       2.99096938
```

输入文件 `run.inp` 如下：

```text
tolerance 2 # 要求原子间距不能小于 2.0 埃
output output.xyz # 指定输出文件
seed -1 # 使用随机种子生成随机结构
filetype xyz # 输出文件的格式
structure model.xyz # 指定输入文件
  number 150 # 分子数
  inside cube 0. 0. 0. 20.88330445 # [xmin ymin zmin d] 控制立方盒子的大小
end structure
```

将 `model.xyz` 和 `run.inp` 放在同一目录，运行 `packmol < run.inp`。空间约束越复杂，装填通常需要越多迭代；若约束互相冲突，则需要先调整模型。

## 怎样理解装填结果

初始密度由粒子数、组成和实际盒体积决定，Packmol 不保证密度一定偏低。体相模型可在相容力场下最小化并通过合适的 NPT 流程调节体积；固定体积、界面与受限体系则按研究模型选择系综，不能统一要求用 NPT 压缩。

上面的两原子 `model.xyz` 在装填时是一个刚性模板，`tolerance` 主要约束不同模板实例之间的原子接触；模板内部的距离不会因此优化。输入中固定范围、输出的盒元数据与真正的周期镜像检查是不同设置。详见[空间分区、周期边界与拓扑对应](空间分区、周期边界与拓扑对应.md)，可运行的例子见[周期水盒与定向水层](../../examples/packmol-regions/README.md)。
