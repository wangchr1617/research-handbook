# LJ 液体热导率的 EMD 与 NEMD 最小案例

配套[笔记](../../../notes/LAMMPS/扩散与输运/LAMMPS热导率的EMD与NEMD计算.md)说明方法、参数与结果解释。

体系为 LJ 液体，约化密度 0.6、温度 1.35、截断 2.5。EMD 用 4000 个原子的立方盒做 Green–Kubo 积分；NEMD 用 8000 个原子、z 方向加长的盒子做 Müller-Plathe 速度交换。两套输入都从 NVT 平衡开始，生产段不使用控温器。

## 运行

需要 LAMMPS（本案例用 30 Sep 2026）与 Python 3 的 numpy、matplotlib。`LMP_EXEC` 可指定程序：

```bash
python3 -m pip install -r requirements.txt
python3 run.py
python3 postprocess.py
```

也可以 `qsub job.pbs`。所附日志的设置是 1 个 MPI 进程、6 个 OpenMP 线程，EMD 约 2 分钟，NEMD 约 3 分钟。`run.py` 会依次执行 `in.emd` 与 `in.nemd`；`postprocess.py` 读取日志与两个 profile 文件，写 `results.json` 和 `result.png`。

## 结果

| 方法 | κ（ε/(τσ)） | 与参考 3.4 的偏差 |
| --- | --- | --- |
| EMD Green–Kubo | 3.502 | +3.0% |
| NEMD Müller-Plathe | 3.425 | +0.7% |

EMD 三个方向分别为 4.770、3.047、2.690，平均 3.502；由 `profile.heatflux` 独立积分得到 3.507，二者一致。NEMD 的生产段累积交换能为 30322.9，平均温差 1.176，横向面积 354.22，κ=3.425。

参考值 3.4 来自 Evans 1986 的 LJ 结果，LAMMPS 的 `examples/KAPPA` 也用它作对照。当前 NEMD 温度剖面中心比两端高约 1.15，应分别检查两条周期传热路径各自的线性区；3.425 是按示例的全局公式得到的有效值，不能当作已收敛的线性响应热导率。要得到更可靠的 NEMD 值，应减小交换频率或增大横向尺寸，并检查剖面线性和温差稳定性。

## 文件

- `in.emd`、`in.nemd`：两套 LAMMPS 输入，末尾分别打印 `EMD_RESULT`、`NEMD_RESULT`。
- `run.py`：顺序运行两段计算。
- `postprocess.py`：解析日志和 profile，核对相关积分与全局通量，绘图。
- `log.*`、`stdout.*`、`profile.*`：本次运行的原生输出。
- `results.json`、`result.png`：后处理结果。
- `data/provenance.json`：命令、耗时、输入输出哈希与平台信息。

`lattice fcc 0.6` 在 LJ 单位下表示约化数密度 0.6，不是晶格常数 0.6；盒长为 18.82σ。把这一点弄错会让体积、面积和 κ 的单位换算全部偏掉。
