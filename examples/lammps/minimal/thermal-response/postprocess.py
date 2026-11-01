"""用法：python3 postprocess.py；分开分析Cu的NPT热膨胀与NVT定容热容。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

KB_EV_K = 8.617333262145e-5
if "Total wall time:" not in Path("lammps.log").read_text():
    raise SystemExit("LAMMPS 未正常结束")
summary = {}
for ensemble in ["npt", "nvt"]:
    rows = []
    for target in [200, 400, 600]:
        x = np.loadtxt(f"samples.{ensemble}.{target}.dat")
        if (
            x.shape != (1001, 5)
            or not np.isfinite(x).all()
            or not np.array_equal(x[:, 0], np.arange(0, 10001, 10))
        ):
            raise SystemExit("热响应采样或时间轴异常")
        values = x[1:, 1:]
        mean = values.mean(axis=0)
        # 五个2ps块只展示短采样波动，不视为充分独立的置信区间。
        block_means = values.reshape(5, 200, 4).mean(axis=1)
        sem = block_means.std(axis=0, ddof=1) / np.sqrt(5)
        if abs(mean[0] - target) / target > 0.1:
            raise SystemExit("平均温度明显偏离目标")
        if ensemble == "nvt" and np.ptp(values[:, 3]) > 1e-6:
            raise SystemExit("定容计算的体积发生变化")
        cv_fluct = 256 * np.var(values[:, 1], ddof=1) / (KB_EV_K * mean[0] ** 2)
        rows.append([target, *mean, *sem, cv_fluct])
    summary[ensemble] = rows
    np.savetxt(
        f"thermal.{ensemble}.dat",
        rows,
        header="target_K mean_T mean_E_eV_atom mean_a_A mean_V_A3 sem_T sem_E sem_a sem_V Cv_fluct_eV_K_atom",
    )
npt = np.array(summary["npt"])
nvt = np.array(summary["nvt"])
slope_a = np.polyfit(npt[:, 1], npt[:, 3], 1)[0]
alpha = slope_a / npt[:, 3].mean()
cv = np.polyfit(nvt[:, 1], nvt[:, 2], 1)[0]
if alpha <= 0 or cv <= 0:
    raise SystemExit("热膨胀或热容斜率异常")
metrics = {
    "atoms": 256,
    "production_ps_per_state": 10,
    "linear_expansion_per_K": float(alpha),
    "fixed_volume_Cv_eV_K_atom": float(cv),
    "fixed_volume_Cv_over_kB_atom": float(cv / KB_EV_K),
    "NVT_fluctuation_Cv_over_kB_atom": (nvt[:, -1] / KB_EV_K).tolist(),
    "states": summary,
}
Path("thermal-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps({k: v for k, v in metrics.items() if k != "states"}, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
