# OVITO Python 批量分析

**适用环境：Windows、macOS、Linux 的 Python 环境；大轨迹后处理在获准计算资源中运行。**

界面里跑通一次分析后，可以用 Python 对多个文件重复执行相同流程。先验证一个小文件，再处理整个目录。

## 一、准备 Python 环境

从 [OVITO 官网](https://ovito.org/)选择 Python module 的安装方式。没有 Conda 时先读 [环境安装](../../getting-started/Anaconda、Miniconda、Mamba安装与使用.md)，下面创建独立环境：

```bash
conda create -n ovito-analysis python=3.12
conda activate ovito-analysis
python -m pip install ovito numpy
python -c "import ovito; print(ovito.version)"
```

OVITO Python 模块可以单独安装，图形应用中的 Python 功能与 Basic / Pro 版本是另一回事。不要把 conda-forge 的 Basic 包和需要 Python API 的环境混为一谈，具体要求以 [官方安装说明](https://ovito.org/)为准。

## 二、写一个按帧统计的脚本

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

应得到一行数据：frame 为 `0`，原子数为 `2`，平均配位数为 `1`。输出使用 `"x"` 模式，已有同名文件时停止，避免无意覆盖上次分析。失败时输出可能只有部分行，不能把文件存在当作全轨迹完成。

## 三、处理多个独立文件

下面在 Bash 中执行，先确认每个输入的结构和单位一致：

```bash
mkdir -p summaries
for file in ./*.dump; do
    [ -f "$file" ] || continue
    name=$(basename "$file" .dump)
    python analyze.py "$file" "summaries/${name}.csv" --cutoff 2.5 || exit 1
done
```

独立文件与单个多帧轨迹是两种组织方式。本脚本逐帧 `compute` 后导出标量，不把整个轨迹转换成一大张坐标数组，内存需求更容易控制。

集群的 Module、容器路径和可用核数按当前环境确认。处理大轨迹通过 [PBS](../../getting-started/PBS作业管理系统使用.md)，已安装包但缺少系统运行库时，使用管理员提供的环境或 [容器](OVITO容器环境配置.md)，不要修改共享系统库。

参考：[OVITO 文件 I/O](https://ovito.org/docs/current/python/introduction/file_io.html)。
