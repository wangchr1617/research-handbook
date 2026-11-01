"""用法：python3 plot.py；比较氧原子自旋参考对 O₂ 解离能的影响。"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

x = json.loads(Path("oxygen-results.json").read_text())
y = [x["electronic_dissociation_eV"], x["incorrect_nonspin_reference_eV"]]
fig, ax = plt.subplots(figsize=(5.5, 3.6), layout="constrained")
ax.bar(["Spin-polarized O", "Non-spin O"], y, color=["#367dac", "#b94e4e"])
ax.set(ylabel="2E(O) - E(O2) (eV)", title="Same O2; different atomic references")
for i, value in enumerate(y):
    ax.text(i, value, f"{value:.3f}", ha="center", va="bottom")
fig.savefig("oxygen-reference.png", dpi=180)
