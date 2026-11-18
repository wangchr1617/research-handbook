# LAMMPS 后处理

**适用环境：Windows / macOS / Linux（Python 数据分析）。**

一份日志可能先最小化、再平衡、最后采样。若直接拿第二个热力学表作图，很容易把温度斜坡当成生产段。可以先列出日志里的各段边界，再决定哪段用于画晶胞尺寸或做统计。

## 一、让输入写出可追溯的热力学表

在 `thermo_style` 后设置 YAML 格式，同时保存步号与时间。后面的示例需要 `PyYAML`、`pandas` 和 `matplotlib`。

```lammps
thermo_style custom step time temp cella cellb cellc
thermo_modify line yaml
```

## 二、先核对表头和范围，再选绘图段

下面的代码先列出各段信息。参照输入中的 `run`、`minimize` 与 `reset_timestep` 确认目标段，再将 `run_index` 改成对应的编号。

```python
import re, yaml
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.size'] = 14
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'

try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

docs = ""
with open("log.lammps") as f:
    for line in f:
        m = re.search(r"^(keywords:.*$|data:$|---$|\.\.\.$|  - \[.*\]$)", line)
        if m: docs += m.group(0) + '\n'

thermo = list(yaml.load_all(docs, Loader=Loader))

for index, block in enumerate(thermo):
    keywords = block["keywords"]
    rows = block["data"]
    if rows:
        print(index, keywords, len(rows), rows[0], rows[-1])

run_index = 1  # 示例值，按上面的列表选择目标段。
if not 0 <= run_index < len(thermo):
    raise ValueError("run_index does not match a block in the log")
block = thermo[run_index]
df = pd.DataFrame(block["data"], columns=block["keywords"])
required = {"Temp", "Cella", "Cellb", "Cellc"}
if df.empty or not required.issubset(df.columns):
    raise ValueError("selected block has no data or is missing temperature/cell columns")
df.plot(x="Temp", y=["Cella", "Cellb", "Cellc"], ylabel="Cell length")
plt.savefig("cell_length.png", bbox_inches="tight")
```

例如[热膨胀与定容热容](../结构与热力学/LAMMPS热膨胀与定容热容.md)采用多个独立温度点。若要算热膨胀，应先在各温度的生产段求平均，再拟合温度与晶胞尺寸。单段的瞬时温度和晶胞涨落图更适合排查平衡状态。抽查首末步号还可发现中途终止或重置步号造成的拼接错误。
