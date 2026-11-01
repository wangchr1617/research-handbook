"""用法：python3 postprocess.py；交叉核对展开坐标 MSD，并比较两个扩散拟合窗口。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read

if "Total wall time:" not in Path("lammps.log").read_text():
    raise SystemExit("LAMMPS 未正常结束")
x = np.loadtxt("msd.dat")
energy = np.loadtxt("energy.dat")
frames = read("trajectory.dump", index=":", format="lammps-dump-text")
if x.shape != (101, 5) or len(frames) != 101 or energy.shape != (101, 3):
    raise SystemExit("采样行数或轨迹帧数异常")
if (
    not np.isfinite(x).all()
    or not np.isfinite(energy).all()
    or not np.array_equal(x[:, 0], np.arange(0, 10001, 100))
):
    raise SystemExit("时间轴或采样数值异常")
reference = frames[0].positions
independent = []
for a in frames:
    displacement = a.positions - reference
    displacement -= displacement.mean(axis=0)
    independent.append(np.mean(np.sum(displacement**2, axis=1)))
error = float(np.max(np.abs(independent - x[:, 4])))
if not np.allclose(independent, x[:, 4], rtol=2e-6, atol=1e-6):
    raise SystemExit("展开坐标重算 MSD 与 LAMMPS 不一致")
time = x[:, 0] * 0.005
fits = []
for start, stop in [(10, 30), (20, 50)]:
    mask = (time >= start) & (time <= stop)
    slope, intercept = np.polyfit(time[mask], x[mask, 4], 1)
    prediction = slope * time[mask] + intercept
    r2 = 1 - np.sum((x[mask, 4] - prediction) ** 2) / np.sum(
        (x[mask, 4] - x[mask, 4].mean()) ** 2
    )
    if slope <= 0 or r2 < 0.9:
        raise SystemExit("拟合区间未呈现清晰的扩散增长")
    fits.append(
        {
            "interval_reduced_time": [start, stop],
            "D_reduced": float(slope / 6),
            "r_squared": float(r2),
        }
    )
drift = float(np.ptp(energy[:, 2]) / 256)
if drift > 0.01:
    raise SystemExit("NVE 每原子总能漂移偏大，请缩短步长")
metrics = {
    "atoms": 256,
    "production_steps": 10000,
    "mean_temperature_reduced": float(energy[:, 1].mean()),
    "energy_range_epsilon_per_atom": drift,
    "MSD_crosscheck_max_sigma2": error,
    "fits": fits,
}
Path("diffusion-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
np.savetxt(
    "msd-plot.dat", np.column_stack([time, x[:, 4]]), header="time_tau MSD_sigma2"
)
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
