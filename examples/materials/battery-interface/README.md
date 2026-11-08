# 界面黏附功与 SEI 电子隧穿

配套[笔记](../../../notes/材料应用/锂离子电池/锂电池界面与SEI.md)说明界面参考态、能带对齐与 SEI 的电子/离子输运。

`data/input.json` 中的 slab、界面能量和势垒是**为检查代码而构造的示意数值，不是真实界面数据**。程序算黏附功 $W_{\rm ad}=(E_A+E_B-E_{A/B})/A$，并用方势垒估算电子透射率 $T\approx e^{-2\kappa L}$。

## 运行

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

输出 `results.json` 与 `result.png`。左图是三个界面的黏附功，右图是透射率随 SEI 厚度的变化。

## 输入

- `interfaces[].E_slab_a_eV`、`E_slab_b_eV`：两块 slab 的总能量（含自由表面）。
- `interfaces[].E_interface_eV`：拼合后的界面总能量。
- `interfaces[].area_A2`：界面面积。
- `tunneling.barrier_eV`：电子势垒高度；`effective_mass_m_e`：有效质量（以电子质量为单位）。
- `tunneling.thickness_nm`：SEI 厚度列表。

换成自己的数据时，slab 厚度、真空层、终止面和偶极修正必须与界面计算一致。势垒高度应来自能带对齐，不要把 Kohn–Sham 带隙直接当势垒。

## 本次示意结果

- Li|Li2CO3 黏附功约 0.80 J/m²；Li2CO3|电解液约 1.76 J/m²；Li|电解液约 0.64 J/m²。
- 3 eV 势垒、单位有效质量时，衰减长度约 0.056 nm；1 nm 处透射率约 $2\times10^{-8}$。

这些数字只用于验证代码路径。

## 检查

- 黏附功为正是否代表结合稳定？参考态是否一致？
- 透射率是否随厚度指数下降？势垒和有效质量是否合理？
- 是否把 SEI 当成均匀方势垒？真实体系的缺陷态、能带弯曲和空间电荷会改变结果。
