# 二维 kMC：从跃迁势垒到扩散系数

配套[笔记](../../../notes/材料应用/锂离子电池/锂电池多尺度计算方法.md)说明 DFT→MD→kMC→连续模型的交接。

示例是二维格点上的示踪粒子：x、y 方向势垒不同，按过渡态理论算跃迁速率，用速率加权选择事件、指数分布推进时间，再由 MSD 提取扩散系数并做 Arrhenius 拟合。势垒是**示意输入**，不是真实材料参数。

## 运行

```bash
python3 -m pip install -r requirements.txt
python3 run.py
```

约几秒到几十秒，取决于轨迹数。输出 `results.json` 与 `result.png`。

## 输入

- `barrier_x_eV`、`barrier_y_eV`：两个方向的跃迁势垒。
- `attempt_frequency_s`：尝试频率。
- `temperatures_K`：温度列表。
- `steps`、`samples`、`tracers`：每条轨迹的事件数、采样点数、独立轨迹数。
- `lattice_constant_A`：跃迁距离，用于把格点 MSD 换成物理单位。

## 本次结果

- 400–800 K 的 $D$ 从约 $1.1\times10^{-11}$ 增到 $2.0\times10^{-9}$ m²/s。
- Arrhenius 拟合 $E_a\approx0.36$ eV，接近 x 方向的 0.35 eV；快方向主导长时扩散，各向异性体系的斜率不对应单一势垒。

## 检查

- 事件表是否完整？漏掉低势垒路径会改变长时扩散。
- 轨迹数是否足够？单条轨迹的 MSD 涨落很大。
- 是否用固定时间步代替 kMC 的时间推进？两者在长时间尺度上不等价。
- 拟合出的活化能是否能对应到具体微观机制？
