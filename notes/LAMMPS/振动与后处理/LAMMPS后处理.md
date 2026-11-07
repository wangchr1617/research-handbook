# LAMMPS 后处理

**适用环境：Windows / macOS / Linux（Python 数据分析）。**

## 提取热力学量

在 LAMMPS 输入中设置 `thermo_modify line yaml`，可将自定义热力学量写成 YAML，便于 Python 从 `log.lammps` 提取。下面读取各个运行段，并以其中一段的温度与晶胞参数作图：

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

print("Number of runs: ", len(thermo))
print("Columns of run 0: ", thermo[0]['keywords'][:])

print("-----------------------------")

df = pd.DataFrame(data=thermo[1]['data'], columns=thermo[1]['keywords'])
fig = df.plot(x='Temp', y=['Cella', 'Cellb', 'Cellc',], ylabel='Cell length')
plt.savefig('cell_length.png', bbox_inches='tight')
```
