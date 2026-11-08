# 二维 Ising 蒙特卡罗

配套[磁性与自旋模型](../../../notes/固体物理基础/磁性与自旋模型.md)。

模型：$32\times32$ 方格，周期性边界，$J=1$，Metropolis 棋盘格更新。测量 $\langle|m|\rangle$、磁化率 $\chi$ 和每自旋能量，扫描 1.6–3.0 的温度。

运行：

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

输出 `results.json` 与 `result.png`。本次采样 $\chi$ 峰在 2.35，精确二维 Ising 临界温度是 $2/\ln(1+\sqrt2)\approx2.269$；差异来自 $L=32$ 的有限尺寸和较粗的温度网格。

检查：增大 $L$ 或加密温度点，峰位应向 2.269 靠近；$T\gg T_c$ 时磁化强度应趋近零。
