# Wigner-Seitz 缺陷分析

**适用环境：OVITO Python（示例按 3.17 API）；Windows / macOS 本机小测试，Linux 集群批处理。**

辐照轨迹的原子总数可能一直相同，但其中一个格点失去原子，另一个格点附近多了一个。Wigner–Seitz 分析将当前原子分配给参考格点，正好能把这两种变化分开。下面先在四格点模型中移动一个原子，用手算结果验收流程，再换成无缺陷参考晶格和实际轨迹。

## 一、区分格点与原子

当 `output_displaced=False` 时，输出的是参考格点：`Occupancy=0` 表示空位格点，`Occupancy=1` 表示正常占据，`Occupancy>1` 表示多重占据格点。

空位数是占据数为零的格点数；过量原子数为所有格点的 $\max(n_i-1,0)$ 之和。一个格点占据数为 3 时，对应两个过量原子，不能简单把“多重占据格点个数”叫作间隙原子总数。

## 二、生成可核对的小输入

先按 [OVITO Python](OVITOPython批量分析.md#一准备-python-环境)安装。将下面内容保存为 `make_ws_demo.py`，在新练习目录执行 `python make_ws_demo.py`：

```python
from pathlib import Path

reference = [(0, 0, 0), (3, 0, 0), (0, 3, 0), (0, 0, 3)]
displaced = [(0, 0, 0), (0.2, 0, 0), (0, 3, 0), (0, 0, 3)]
for name, positions in [("reference.dump", reference), ("displaced.dump", displaced)]:
    lines = ["ITEM: TIMESTEP", "0", "ITEM: NUMBER OF ATOMS", "4",
             "ITEM: BOX BOUNDS pp pp pp", "0 12", "0 12", "0 12",
             "ITEM: ATOMS id type x y z"]
    lines += [f"{i} 1 {x} {y} {z}" for i, (x, y, z) in enumerate(positions, 1)]
    Path(name).write_text("\n".join(lines) + "\n", encoding="utf-8")
```

这是人工格点演示。第二个原子距第一个格点 0.2 Å，距原来的格点 2.8 Å，因此四个格点按参考顺序的占据数应为 `[2, 0, 1, 1]`。统计得到一个空位和一个过量原子，而四个原子都还在盒里。

## 三、显式加载参考结构并统计

保存为 `count_ws.py`：

```python
import argparse
import csv
import numpy as np
from ovito.io import import_file
from ovito.pipeline import FileSource
from ovito.modifiers import WignerSeitzAnalysisModifier


def main():
    parser = argparse.ArgumentParser(description="Count vacancies and excess atoms")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="ws-counts.csv")
    args = parser.parse_args()
    pipeline = import_file(args.input)
    modifier = WignerSeitzAnalysisModifier(output_displaced=False)
    modifier.reference = FileSource()
    modifier.reference.load(args.reference)
    pipeline.modifiers.append(modifier)
    with open(args.output, "x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frame", "vacancies", "excess_atoms"])
        for frame in range(pipeline.source.num_frames):
            data = pipeline.compute(frame)
            occupancy = np.asarray(data.particles["Occupancy"], dtype=np.int64)
            vacancies = int(np.count_nonzero(occupancy == 0))
            excess = int(np.maximum(occupancy - 1, 0).sum())
            writer.writerow([frame, vacancies, excess])
            print(frame, vacancies, excess)


if __name__ == "__main__":
    main()
```

```bash
python count_ws.py --reference reference.dump --input displaced.dump --output ws-counts.csv
```

`FileSource` 负责读取外部参考结构，先赋给 `modifier.reference`，再调用 `load()`。本例应输出 `0 1 1`。已有输出文件时会停止，换名后再运行，避免覆盖旧结果。真实轨迹需确保参考与当前结构的晶胞、周期边界和类型映射一致；变胞轨迹是否做仿射映射，按研究定义与 OVITO 参数确认。

## 四、显示和科研解释

显示缺陷时，可在分析后根据 Occupancy 选择格点，把 `0` 显示为蓝色、`>1` 显示为红色，正常占据格点隐藏。先导出数值计数，再为了显示删除或隐藏格点，不从渲染图片估计缺陷数量。

如果希望做逐帧自检，可以核对“过量原子数减空位数”是否等于“当前原子数减参考格点数”。这条恒等式可以用来排查计数口径错误，但参考结构与当前构型的匹配是否合理，仍需结合具体结构判断。对于已有损伤的轨迹，改用第一帧作为参考会改变缺陷的定义。

多组分材料还要区分总占据与类型占据，反位缺陷可能不改变总 Occupancy。热振动、整体漂移、形变与参考选择都会影响解释，先在已知无缺陷结构和人为引入缺陷的小例子中核对。

大轨迹通过 [PBS](../../getting-started/PBS作业管理系统使用.md)处理，所需环境可由 [容器](OVITO容器环境配置.md)提供。软件路径和队列按实际集群确认。

参考：[OVITO Wigner-Seitz 原理](https://www.ovito.org/manual/reference/pipelines/modifiers/wigner_seitz_analysis.html)、[Python 修改器](https://ovito.org/docs/current/python/modules/ovito_modifiers.html#ovito.modifiers.WignerSeitzAnalysisModifier)。
