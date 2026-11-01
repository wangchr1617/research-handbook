"""用法：python3 postprocess.py；检查正常结束并提取能量、频率或激发谱。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

MODE = "geometry-frequency"
text = Path("orca.out").read_text(errors="replace")
if "ORCA TERMINATED NORMALLY" not in text or "SCF NOT CONVERGED" in text:
    raise SystemExit("ORCA 未正常完成或 SCF 未收敛")
energies = [
    float(x) for x in re.findall(r"FINAL SINGLE POINT ENERGY\s+(-?[\d.]+)", text)
]
if not energies or not np.isfinite(energies).all():
    raise SystemExit("未找到有效能量")
result = {"energy_hartree": energies[-1], "mode": MODE}
if MODE == "geometry-frequency":
    if "THE OPTIMIZATION HAS CONVERGED" not in text:
        raise SystemExit("几何优化未收敛")
    freq = np.array(
        [
            float(x)
            for x in re.findall(r"^\s*\d+:\s+(-?[\d.]+)\s+cm", text, re.MULTILINE)
        ]
    )
    if len(freq) != 9 or np.any(freq < -20):
        raise SystemExit("水分子频率数或虚频异常")
    result["vibrational_frequencies_cm-1"] = freq[-3:].tolist()
    fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
    ax.bar(range(1, 4), freq[-3:], color="#3178a8")
    ax.set(xlabel="Vibrational mode", ylabel="Frequency (cm$^{-1}$)", xticks=[1, 2, 3])
    fig.savefig("result.png", dpi=180)
elif MODE == "tddft":
    # ORCA 原生电偶极吸收表包含能量、波长与振子强度。
    section = text.split("ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS")[
        -1
    ]
    lines = []
    for line in section.splitlines():
        parts = line.split()
        if len(parts) >= 10 and parts[1] == "->":
            try:
                lines.append([float(v) for v in [parts[3], parts[5], parts[6]]])
            except ValueError:
                continue
        if len(lines) == 5:
            break
    if len(lines) != 5:
        raise SystemExit("未读到五个原生激发跃迁，请核对输出表格式")
    data = np.array(lines)
    np.savetxt(
        "transitions.dat", data, header="energy_eV wavelength_nm oscillator_strength"
    )
    result["transitions"] = data.tolist()
    ev = data[:, 0]
    grid = np.linspace(max(0, ev.min() - 1), ev.max() + 1, 1000)
    width = 0.15  # eV，高斯展宽仅用于显示。
    spectrum = np.sum(
        data[:, 2, None] * np.exp(-0.5 * ((grid[None, :] - ev[:, None]) / width) ** 2),
        axis=0,
    )
    fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
    ax.plot(grid, spectrum, color="#3178a8")
    ax.vlines(ev, 0, data[:, 2], color="#d7792a", alpha=0.7)
    ax.set(
        xlabel="Excitation energy (eV)",
        ylabel="Oscillator strength / broadened intensity",
    )
    fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
