"""用法：python3 postprocess.py；提取响应系数，检查物理定义并绘图。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HARTREE_EV = 27.211386245988
for name in json.loads(Path("stages.json").read_text()):
    if "Total wall time:" not in (Path(name) / "lammps.out").read_text():
        raise SystemExit(f"{name}未正常结束")
xminus = np.loadtxt("xminus/stress.dat")
xplus = np.loadtxt("xplus/stress.dat")
sminus = np.loadtxt("sminus/stress.dat")
splus = np.loadtxt("splus/stress.dat")
# LAMMPS压力与拉伸为正的应力符号相反；工程剪切gamma用于C44。
C11 = -(xplus[0] - xminus[0]) / 0.002
C12 = -(xplus[1] - xminus[1]) / 0.002
C44 = -(splus[3] - sminus[3]) / 0.002
result = {
    "C11_reduced": float(C11),
    "C12_reduced": float(C12),
    "C44_reduced": float(C44),
    "bulk_modulus_reduced": float((C11 + 2 * C12) / 3),
}
if not (C11 > C12 and C44 > 0 and C11 + 2 * C12 > 0):
    raise SystemExit("立方弹性稳定性检查未通过")
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.bar(["C11", "C12", "C44"], [C11, C12, C44])
ax.set(ylabel="Elastic constant (ε/σ³)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
