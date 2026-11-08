# 一维双原子链的声子色散

配套[晶格振动与声子谱](../../../notes/固体物理基础/晶格振动与声子谱.md)。

模型：质量 $m_1$、$m_2$ 交替，最近邻弹簧常数 $K$，色散

$$
\omega^2=K\left(\frac1{m_1}+\frac1{m_2}\right)
\pm K\sqrt{\left(\frac1{m_1}+\frac1{m_2}\right)^2-\frac{4\sin^2(qa/2)}{m_1m_2}}.
$$

运行：

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

默认 $m_1=1$、$m_2=2$、$K=1$ 给出带隙下边 $\sqrt{2K/m_{\rm heavy}}=1.0$、上边 $\sqrt{2K/m_{\rm light}}\approx1.414$（模型频率单位）。DOS 直方图按概率密度归一化。声学支在 $\Gamma$ 点为零，光学支在 $\Gamma$ 点最高。

检查：$m_1=m_2$ 时带隙应关闭；$K$ 加倍时所有频率应乘 $\sqrt2$。
