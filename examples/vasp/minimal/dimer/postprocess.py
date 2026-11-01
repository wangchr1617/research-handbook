"""用法：python3 postprocess.py；核对 Dimer 与受约束振动，输出鞍点诊断图。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read

subprocess.run([sys.executable, "check_vasp.py"], check=True)
subprocess.run(
    [sys.executable, str(Path("check_vasp.py").resolve())], cwd="frequency", check=True
)
out = Path("OUTCAR").read_text()
if "reached required accuracy" not in out:
    raise SystemExit("Dimer 未达到受力阈值")
curvatures = [
    float(x)
    for x in re.findall(r"curvature along the dimer direction:\s*([-0-9.]+)", out)
]
gradients = [float(x) for x in re.findall(r"max. gradient \(eV/A\):\s*([-0-9.]+)", out)]
a, b = read("POSCAR"), read("CONTCAR")
delta = b.get_scaled_positions() - a.get_scaled_positions()
delta -= np.rint(delta)
frozen_drift = np.linalg.norm((delta @ a.cell)[1:], axis=1).max()
freqout = Path("frequency/OUTCAR").read_text()
modes = [
    (bool(imag), float(value))
    for imag, value in re.findall(r"f( /i|/i)?\s*=\s*([0-9.]+)\s+THz", freqout)
]
# NWRITE=3 同时输出两套本征矢；频率应相同，仅保留一组。
if len(modes) == 6 and modes[:3] == modes[3:]:
    modes = modes[:3]
if len(modes) != 3:
    raise SystemExit(f"预期三个自由度的频率，实际 {modes}")
freq = np.array([-v if imag else v for imag, v in modes])
if not curvatures or curvatures[-1] >= 0 or not gradients or gradients[-1] >= 0.02:
    raise SystemExit("负曲率或梯度检查未通过")
if frozen_drift > 1e-8 or (freq < -0.1).sum() != 1 or (freq > 0.1).sum() != 2:
    raise SystemExit("固定原子位移或一阶鞍点检查未通过")
metrics = {
    "last_reported_curvature_eV_A2": curvatures[-1],
    "final_gradient_eV_A": gradients[-1],
    "frozen_drift_A": float(frozen_drift),
    "signed_frequencies_THz": freq.tolist(),
    "final_migrating_atom_fractional": b.get_scaled_positions()[0].tolist(),
}
Path("dimer-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
np.savetxt("dimer-gradients.dat", gradients, header="reported_max_gradient_eV_A")
np.savetxt("dimer-frequencies.dat", freq, header="signed_frequency_THz")
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
