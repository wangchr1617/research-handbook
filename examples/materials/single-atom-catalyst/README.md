# 单原子与二聚体的稳定性

配套[笔记](../../../notes/材料应用/电催化/单原子与双原子催化剂建模.md)说明形成能、化学势与二聚化能。

`data/input.json` 中的总能量是**为检查代码而构造的示意数值，不是真实催化剂数据**。程序算单原子形成能 $E_f=E_{\rm M@support}-E_{\rm support}-\mu_M$ 和二聚化能 $\Delta E=E_{\rm M_2@support}+E_{\rm support}-2E_{\rm M@support}$。

## 运行

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

输出 `results.json` 与 `result.png`。左图是单原子与二聚体（每原子）的形成能随金属化学势的变化，右图是结合能与二聚化能。

## 输入

- `E_support_eV`：干净载体的总能量。
- `E_single_atom_eV`：同一载体上放一个金属原子的总能量。
- `E_dimer_eV`：同一载体上放两个金属原子的总能量。
- `E_bulk_per_atom_eV`：金属本体的每原子能量，作为 $\mu_M$ 的上限。
- `mu_min_eV`、`mu_max_eV`：画图用的化学势范围。

换成自己的数据时，所有总能量必须用同一 slab、截断、k 点和泛函；二聚化能的配平要包含干净载体。

## 本次示意结果

- $\mu_M=E_{\rm bulk}=-5$ eV 时，单原子形成能 $-1$ eV。
- 二聚化能 $+1$ eV，单原子在热力学上比二聚体稳定。
- 这些数字只用于验证代码路径。

## 检查

- 形成能是否为负？对应哪个 $\mu_M$？
- 二聚化能是否小于零？有没有算更大团簇？
- 超胞尺寸、覆盖度和自旋态是否影响结论？
- 吸附中间体后，单原子/双原子是否仍然稳定？
