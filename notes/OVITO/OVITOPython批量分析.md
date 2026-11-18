# OVITO Python 批量分析

**适用环境：Windows、macOS、Linux 的 Python 环境；大轨迹后处理在获准计算资源中运行。**

在 OVITO 界面里给两个原子加上配位分析后，两边都应该显示一个邻居。要把同一套分析用到几百帧，可以先让 Python 读入同一个两原子文件，对比界面和 CSV 的结果。这个小例子把导入、截断半径和统计口径锁定下来，发现差异时也容易定位。

## 一、准备 Python 环境

从 [OVITO 官网](https://ovito.org/)选择 Python module 的安装方式。没有 Conda 时先读 [环境安装](../../getting-started/Anaconda、Miniconda、Mamba安装与使用.md)，下面创建独立环境：

```bash
conda create -n ovito-analysis python=3.12
conda activate ovito-analysis
python -m pip install ovito numpy
python -c "import ovito; print(ovito.version)"
```

OVITO Python 模块可以单独安装，图形应用中的 Python 功能与 Basic / Pro 版本是另一回事。不要把 conda-forge 的 Basic 包和需要 Python API 的环境混为一谈，具体要求以 [官方安装说明](https://ovito.org/)为准。

## 二、把界面上的配位数对回第一行 CSV

先把 [基础操作](OVITO安装与基础操作.md)里的 `two-atoms.dump` 放入新练习目录。保存以下脚本为 `analyze.py`：

```python
import argparse
import csv
from pathlib import Path
import numpy as np
from ovito.io import import_file
from ovito.modifiers import CoordinationAnalysisModifier


def main():
    parser = argparse.ArgumentParser(description="Mean coordination for every frame")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cutoff", type=float, required=True)
    args = parser.parse_args()
    if args.cutoff <= 0:
        raise ValueError("cutoff must be positive")
    if args.input.resolve() == args.output.resolve():
        raise ValueError("input and output must differ")
    pipeline = import_file(str(args.input))
    pipeline.modifiers.append(CoordinationAnalysisModifier(cutoff=args.cutoff))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frame", "atoms", "mean_coordination"])
        for frame in range(pipeline.source.num_frames):
            data = pipeline.compute(frame)
            if data.particles.count == 0:
                raise ValueError(f"empty frame: {frame}")
            mean = np.asarray(data.particles["Coordination"]).mean()
            writer.writerow([frame, data.particles.count, float(mean)])


if __name__ == "__main__":
    main()
```

```bash
python analyze.py two-atoms.dump outputs/coordination.csv --cutoff 2.5
```

应得到一行数据：frame 为 `0`，原子数为 `2`，平均配位数为 `1`。输出使用 `"x"` 模式，已有同名文件时停止，避免无意覆盖上次分析。失败时输出可能只有部分行。先检查脚本退出状态和 CSV 数据行数，再与源轨迹帧数核对。确认失败输出不再使用后，可换一个文件名重跑。CSV 的 frame 从 0 开始，是读取顺序；若后续需要物理时间，应另外保留 dump 时步及换算关系。

## 三、批处理前核对帧号和完成状态

下面在 Bash 中执行，先确认每个输入的结构和单位一致：

```bash
mkdir -p summaries
for file in ./*.dump; do
    [ -f "$file" ] || continue
    name=$(basename "$file" .dump)
    python analyze.py "$file" "summaries/${name}.csv" --cutoff 2.5 || exit 1
done
```

若目录下的每个文件是一段单独的轨迹，每份输出的帧号都会从 0 开始。合并结果时同时保留源文件名。本脚本逐帧 `compute` 后导出标量，不把整个轨迹转换成一大张坐标数组，内存需求更容易控制。

集群的 Module、容器路径和可用核数按当前环境确认。处理大轨迹通过 [PBS](../../getting-started/PBS作业管理系统使用.md)，已安装包但缺少系统运行库时，使用管理员提供的环境或 [容器](OVITO容器环境配置.md)，不要修改共享系统库。

两原子案例跑通后，可以用[简单立方配位与 RDF](配位数与径向分布函数.md)检查周期边界和多个近邻壳层。

参考：[OVITO 文件 I/O](https://ovito.org/docs/current/python/introduction/file_io.html)。
