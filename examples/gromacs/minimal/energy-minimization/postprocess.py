"""用法：python3 postprocess.py；调用 gmx energy/msd，并检查时间轴、绘图。"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

MODE = "energy-minimization"
exe = shutil.which(os.environ.get("GMX_EXEC", "gmx"))
stage = {"energy-minimization": "em", "nvt": "nvt", "npt": "npt", "diffusion": "md"}[
    MODE
]
log = Path(stage + ".log").read_text()
if MODE == "energy-minimization":
    if "converged to Fmax" not in log:
        raise SystemExit("最小化未达到最大力标准")
elif "Finished mdrun" not in log:
    raise SystemExit("动力学未正常完成")
if re.search(r"LINCS WARNING|Fatal error|\bnan\b", log, re.IGNORECASE):
    raise SystemExit("日志含约束、数值或致命错误")
selection = (
    "Potential\n0\n"
    if MODE == "energy-minimization"
    else "Temperature\nPotential\n" + ("Density\n" if MODE == "npt" else "") + "0\n"
)
with Path("energy-analysis.log").open("w") as out:
    subprocess.run(
        [exe, "energy", "-f", stage + ".edr", "-o", "energy.xvg", "-xvg", "none"],
        input=selection,
        text=True,
        stdout=out,
        stderr=subprocess.STDOUT,
        check=True,
    )
x = np.loadtxt("energy.xvg")
if x.ndim != 2 or not np.isfinite(x).all():
    raise SystemExit("能量数据格式异常")
result = {"mode": MODE, "samples": len(x)}
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
if MODE == "energy-minimization":
    result.update(
        initial_potential_kJ_mol=float(x[0, 1]), final_potential_kJ_mol=float(x[-1, 1])
    )
    if x[-1, 1] >= x[0, 1]:
        raise SystemExit("势能未下降")
    ax.plot(x[:, 0], x[:, 1])
    ax.set(xlabel="Minimization pseudo-time (ps)", ylabel="Potential energy (kJ/mol)")
else:
    expected = 20 if MODE == "diffusion" else 5
    if abs(x[-1, 0] - expected) > 1e-5:
        raise SystemExit("动力学时间轴不完整")
    result["mean_temperature_K"] = float(x[len(x) // 2 :, 2].mean())
    if not 250 < result["mean_temperature_K"] < 350:
        raise SystemExit("平均温度偏离目标")
    if MODE == "npt":
        result["mean_density_kg_m3"] = float(x[len(x) // 2 :, 3].mean())
        ax.plot(x[:, 0], x[:, 3])
        ax.set(xlabel="Time (ps)", ylabel="Density (kg/m$^3$)")
    elif MODE == "nvt":
        ax.plot(x[:, 0], x[:, 2])
        ax.axhline(300, color="gray", ls="--")
        ax.set(xlabel="Time (ps)", ylabel="Temperature (K)")
    else:
        with Path("msd-analysis.log").open("w") as out:
            subprocess.run(
                [
                    exe,
                    "msd",
                    "-s",
                    "md.tpr",
                    "-f",
                    "md.xtc",
                    "-o",
                    "msd.xvg",
                    "-sel",
                    "res_com of resname SOL",
                    "-trestart",
                    "1",
                    "-maxtau",
                    "10",
                    "-beginfit",
                    "2",
                    "-endfit",
                    "8",
                    "-xvg",
                    "none",
                ],
                stdout=out,
                stderr=subprocess.STDOUT,
                check=True,
            )
        msd = np.loadtxt("msd.xvg")
        mask = (msd[:, 0] >= 2) & (msd[:, 0] <= 8)
        slope, intercept = np.polyfit(msd[mask, 0], msd[mask, 1], 1)
        if slope <= 0:
            raise SystemExit("MSD拟合斜率异常")
        result["D_nm2_ps"] = float(slope / 6)
        ax.plot(msd[:, 0], msd[:, 1], label="gmx msd, water COM")
        ax.plot(
            msd[mask, 0], slope * msd[mask, 0] + intercept, ls="--", label="Fit: 2–8 ps"
        )
        ax.set(xlabel="Lag time (ps)", ylabel="MSD (nm$^2$)")
        ax.legend()
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
