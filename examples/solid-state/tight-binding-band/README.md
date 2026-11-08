# 二聚化链的能带与态密度

配套[能带结构与紧束缚模型](../../../notes/固体物理基础/能带结构与紧束缚模型.md)。

模型：每个晶胞两个格点，胞内跃迁 $t_1$、胞间 $t_2$，色散

$$
E_\pm(k)=\pm\sqrt{t_1^2+t_2^2+2t_1t_2\cos(ka)}.
$$

运行：

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

输出 `results.json` 与 `result.png`。默认参数 $t_1=1$、$t_2=0.6$ eV 给出带隙 $2|t_1-t_2|=0.8$ eV、带宽 $2(t_1+t_2)=3.2$ eV；态密度在带边发散，带隙内为零。

检查：把 $t_2$ 设为 $t_1$，带隙应关闭；把 $t_2$ 设为 0，上下带应变成两条平带。
