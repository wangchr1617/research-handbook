# OER 描述符火山图

配套[笔记](../../../notes/材料应用/电催化/电催化描述符与火山图.md)说明描述符、标度关系与火山图。

`data/input.json` 中的标度关系是**为画图而设的示意式，不是 OER 的通用规律**。程序只做几何后处理：由四步 CHE 台阶和线性标度关系算过电位。

## 运行

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

输出 `results.json` 与 `result.png`。左图是沿一条示意标度关系的 1D 火山，右图是 $\Delta G_{\rm OH}$–$\Delta G_{\rm O}$ 的二维过电位图。

## 输入

- `dG_OH_range_eV`：描述符扫描范围。
- `dG_O_ratio`：一维切片用的 $\Delta G_{\rm O}=k\Delta G_{\rm OH}$ 斜率。
- `dG_OOH_offset_eV`：$\Delta G_{\rm OOH}=\Delta G_{\rm OH}+c$ 的截距。

## 本次示意结果

一维火山在 $\Delta G_{\rm OH}=1.60$ eV 处最小，$\eta=0.37$ V。二维图的低谷沿斜带分布；固定一个描述符做切片时，极小值可能落在边界，不能据此判断没有火山。

这些数字只用于验证公式与代码路径，不能引用为真实催化剂的过电位。

## 检查

- 标度关系来自哪个表面/文献？是否适用于当前体系？
- 1D 切片是否沿真实标度关系取，而不是任意固定 $\Delta G_{\rm O}$？
- 过电位是热力学值还是包含活化能？
- 有没有考虑溶剂、电位、覆盖度和表面重构？
- 火山顶候选的稳定性是否单独检查？
