# 位形坐标与光学跃迁

配套[点缺陷与光学跃迁](../../../notes/固体物理基础/点缺陷与光学跃迁.md)。

模型：基态 $E_g=\frac12kQ^2$，激发态 $E_e=E_0+\frac12k(Q-Q_0)^2$，

$$
E_{\rm abs}=E_0+\frac12kQ_0^2,\qquad
E_{\rm em}=E_0-\frac12kQ_0^2,\qquad
E_{\rm abs}-E_{\rm em}=2S\hbar\omega.
$$

运行：

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

默认 $E_0=2.5$ eV、$S=3$、$\hbar\omega=0.05$ eV 给出 $Q_0=0.548$ Å、吸收 2.65 eV、发射 2.35 eV、Stokes 位移 0.30 eV。

检查：$S=0$ 时吸收和发射都回到 $E_0$；$S$ 增大时 Stokes 位移线性增大。
