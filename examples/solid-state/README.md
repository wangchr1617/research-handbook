# 固体物理最小模型

配套[固体物理基础](../../notes/固体物理基础/README.md)的五篇笔记。每个案例用几十行 Python 复现一个核心公式，用来检查量级和读图方式；它们不是第一性原理计算，也不含真实材料参数。

| 案例 | 内容 |
| --- | --- |
| [tight-binding-band](tight-binding-band/README.md) | 二聚化链的能带、带隙与态密度 |
| [phonon-chain](phonon-chain/README.md) | 一维双原子链的声子色散与态密度 |
| [ising-magnetization](ising-magnetization/README.md) | 二维 Ising 蒙特卡罗与磁化率峰 |
| [ferroelectric-double-well](ferroelectric-double-well/README.md) | Landau 双势阱、自发极化与电滞回线 |
| [defect-optical](defect-optical/README.md) | 位形坐标、吸收/发射与 Stokes 位移 |

各目录都有 `data/input.json`、`run.py`、`requirements.txt`、`results.json` 和 `result.png`。运行方式相同：

```bash
cd <case>
python3 -m pip install -r requirements.txt
python3 run.py
```

参数都是示意值；换成自己的参数时，先检查公式的极限行为（如带隙关闭、声学支归零、$S=0$ 时 Stokes 位移为零）。
