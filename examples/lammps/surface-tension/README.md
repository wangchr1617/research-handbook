# LJ 液体表面张力的压力张量法

配套[笔记](../../../notes/LAMMPS/结构与热力学/LAMMPS表面张力与润湿.md)说明公式、单位与误差来源。

体系是 LJ 液膜：三维周期边界，沿 $z$ 设置低密度层，形成两个液-气界面。用全局压力张量计算

$$
\gamma=\frac{L_z}{2}\left[P_{zz}-\frac{P_{xx}+P_{yy}}{2}\right].
$$

本次运行：初始晶格数密度 0.8、平衡目标温度 0.85、1800 原子，NVT 平衡 30k 步，NVE 生产 1M 步。结果为 $\gamma=0.3247\ \epsilon/\sigma^2$，10 个分块平均在 0.21–0.43 之间，块间标准差约 0.07。

## 运行

需要 LAMMPS（本案例用 30 Sep 2026）与 Python 3 的 numpy、matplotlib：

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

`run.py` 调 `lmp -in in.surface`，再调 `postprocess.py`。所附日志的设置是 1 个 MPI 进程、6 个 OpenMP 线程，耗时约 8 分钟。已有日志时可单独运行 `python3 postprocess.py`。`LMP_EXEC` 可指定 LAMMPS 程序；也可以 `qsub job.pbs`。

## 文件

- `in.surface`：LAMMPS 输入，末尾打印 `GAMMA_RESULT`。
- `postprocess.py`：解析日志，画瞬时值与分块平均，写 `results.json` 和 `result.png`。累计平均来自每 10 步采样的 `fix ave/time`，分块平均来自每 100 步记录的生产段热力学表。
- `log.surface`：本次运行的 LAMMPS 日志，`postprocess.py` 从这里读取 `GAMMA_RESULT` 和热力学行。
- `results.json`、`result.png`：后处理结果。

## 检查

- 日志中的 `Created ... atoms` 是否约 1800，盒子横向是否约 10.26？
- 生产段平均温度是否接近平衡目标？沿法向是否形成稳定的液相和蒸气区？
- 瞬时 $\gamma$ 的涨落有多大？分块平均是否围绕同一均值波动？
- 把横向尺寸或液膜厚度加倍，$\gamma$ 是否在误差内不变？

`lattice fcc 0.8` 在 LJ 单位下表示约化数密度 0.8，不是晶格常数 0.8；写成 `fcc 1.70998` 会得到密度约 1.71 的固体，表面张力会完全不对。
