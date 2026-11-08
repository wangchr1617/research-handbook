# Landau 双势阱与电滞回线

配套[铁电性与软模](../../../notes/固体物理基础/铁电性与软模.md)。

模型：

$$
F(P)=\frac{\alpha}{2}P^2+\frac{\beta}{4}P^4-EP,\qquad \alpha=a_0(T-T_c).
$$

程序在 $E=0$ 时给出 $P_s=\sqrt{-\alpha/\beta}$，在 $T<T_c$ 时扫场得到 $P$–$E$ 回线。

运行：

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

输出 `results.json` 与 `result.png`。默认参数下 $P_s(0.4)=0.775$，矫顽场估计 0.097；回线在 $\pm0.1$ 附近跳变。

检查：$T>T_c$ 时回线应变成过原点的直线；把 $\beta$ 改成负值并加六阶项，可得到一级相变。
