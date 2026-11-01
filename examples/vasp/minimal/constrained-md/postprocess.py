"""用法：python3 postprocess.py；检查短 MD 的逐步收敛与 H—H 集体变量。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read

subprocess.run([sys.executable, "check_vasp.py"], check=True)
frames = read("XDATCAR", index=":")
if len(frames) != 8:
    raise SystemExit("MD 帧数不是输入指定的 8 步")
bonds = np.array([a.get_distance(0, 1, mic=True) for a in frames])
if not np.isfinite(bonds).all():
    raise SystemExit("轨迹含非有限坐标")
report = Path("REPORT").read_text()
constrained = Path("ICONST").read_text().split()[-1] == "0"
metrics = {
    "steps": len(frames),
    "bond_interval_A": [float(bonds.min()), float(bonds.max())],
}
if constrained:
    if report.count("SHAKE converged") != 8 or np.max(np.abs(bonds - 0.74)) > 1e-6:
        raise SystemExit("SHAKE 未逐步收敛或键长偏离约束")
    metrics["max_bond_error_A"] = float(np.max(np.abs(bonds - 0.74)))
else:
    if "Metadynamics" not in report or not Path("HILLSPOT").is_file():
        raise SystemExit("未发现实际偏置输出")
    # HILLSPOT 的格式随版本变化，具体高斯参数在下面单独核对。
    metrics["hillspot_lines"] = len(Path("HILLSPOT").read_text().splitlines())
Path("md-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
np.savetxt(
    "md-bond.dat",
    np.column_stack([np.arange(1, 9) * 0.25, bonds]),
    header="time_fs bond_A",
)
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
