"""用法：python3 postprocess.py；解析 OpenMX，DOS 调用官方 DosMain。"""

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

MODE = "density-of-states"
HARTREE_EV = 27.211386245988
text = Path("openmx.out").read_text()
summary = Path("system.out").read_text()
if "The calculation was normally finished." not in text:
    raise SystemExit("OpenMX 未正常结束")
energies = [float(v) for v in re.findall(r"Utot\.\s+(-?[\d.]+)", summary)]
if not energies:
    raise SystemExit("未找到总能")
# 对每个原子步检查最后SCF残差，避免仅以正常结束当作收敛。
blocks = re.split(r"(?=SCF=\s+1\s)", summary)
residuals = []
for block in blocks:
    values = re.findall(r"NormRD=\s+([\d.Ee+-]+)", block)
    if values:
        residuals.append(float(values[-1]))
if not residuals or max(residuals) > 1e-6:
    raise SystemExit("存在未充分收敛的电子步")
result = {
    "mode": MODE,
    "energy_hartree": energies[-1],
    "SCF_final_residuals": residuals,
}
if MODE == "geometry-optimization":
    raw = summary.rsplit("<coordinates.forces", 1)[1].split("coordinates.forces>")[0]
    rows = [line.split() for line in raw.splitlines() if line.strip()]
    rows = [r for r in rows if len(r) >= 8 and r[0].isdigit()]
    if len(rows) != 2:
        raise SystemExit("坐标受力行数异常")
    position = np.array([[float(v) for v in r[2:5]] for r in rows])
    force = np.array([[float(v) for v in r[5:8]] for r in rows])
    result["bond_length_angstrom"] = float(np.linalg.norm(position[1] - position[0]))
    result["max_force_hartree_bohr"] = float(np.linalg.norm(force, axis=1).max())
    if result["max_force_hartree_bohr"] > 1e-4:
        raise SystemExit("优化受力未达阈值")
    fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
    ax.plot(
        np.arange(1, len(energies) + 1),
        (np.array(energies) - energies[-1]) * HARTREE_EV,
        "o-",
    )
    ax.set(xlabel="Geometry step", ylabel="Energy above final (eV)")
    fig.savefig("result.png", dpi=180)
elif MODE == "band-structure":
    lines = Path("system.Band").read_text().splitlines()
    nband, spin, fermi = lines[0].split()
    if int(spin) != 0:
        raise SystemExit("本解析器针对非自旋极化例子")
    reciprocal = np.array([float(v) for v in lines[1].split()]).reshape(3, 3)
    nsegment = int(lines[2])
    specs = [line.split() for line in lines[3 : 3 + nsegment]]
    cursor = 3 + nsegment
    points = []
    bands = []
    for spec in specs:
        for _ in range(int(spec[0])):
            header = lines[cursor].split()
            cursor += 1
            if int(header[0]) != int(nband):
                raise SystemExit("能带数变化")
            points.append([float(v) for v in header[1:4]])
            vals = []
            while len(vals) < int(nband):
                vals.extend(float(v) for v in lines[cursor].split())
                cursor += 1
            bands.append(vals)
    eigen = (np.array(bands) - float(fermi)) * HARTREE_EV
    kcart = np.array(points) @ reciprocal
    distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(kcart, axis=0), axis=1))]
    result["path_gap_eV"] = float(eigen[:, 4].min() - eigen[:, 3].max())
    np.savetxt(
        "bands.dat",
        np.column_stack([distance, eigen]),
        header="k_path_distance_bohr-1 bands_eV_relative_to_EF",
    )
    fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
    ax.plot(distance, eigen, color="#3178a8", lw=0.8)
    ax.axhline(0, color="gray", ls="--")
    edge = int(specs[0][0]) - 1
    ax.set(
        ylim=(-12, 8),
        ylabel="$E-E_F$ (eV)",
        xticks=[distance[0], distance[edge], distance[-1]],
        xticklabels=["L", "Γ", "X"],
    )
    ax.axvline(distance[edge], color="gray", lw=0.5)
    fig.savefig("result.png", dpi=180)
elif MODE == "density-of-states":
    exe = shutil.which(os.environ.get("DOSMAIN_EXEC", "DosMain"))
    if exe is None:
        raise SystemExit("请把官方 DosMain 加入 PATH，或设置 DOSMAIN_EXEC")
    for name, answers in [
        ("total", "2\n0.15\n1\n"),
        ("projected", "2\n0.15\n2\n1 2\n"),
    ]:
        with Path("dos-" + name + ".log").open("w") as out:
            subprocess.run(
                [exe, "system.Dos.val", "system.Dos.vec"],
                input=answers,
                text=True,
                stdout=out,
                stderr=subprocess.STDOUT,
                check=True,
            )
    data = np.loadtxt("system.DOS.Gaussian")
    if data.shape[1] != 3 or not np.isfinite(data).all() or data[:, 1].max() <= 0:
        raise SystemExit("DOS 数据异常")
    projected = sum(
        np.loadtxt(f"system.PDOS.Gaussian.atom{atom}")[:, 1] for atom in [1, 2]
    )
    if not np.allclose(projected, data[:, 1], atol=2e-6, rtol=1e-5):
        raise SystemExit("原生PDOS求和与总DOS不一致")
    result["PDOS_sum_max_error_states_eV"] = float(np.max(abs(projected - data[:, 1])))
    # 第三列为截至当前能量的累计态数，非自旋极化输出已包含两种自旋。
    result["integrated_states_at_upper_bound"] = float(data[-1, 2])
    fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
    ax.plot(data[:, 0], data[:, 1], label="Total DOS", color="#3178a8")
    for angular, count in [("s", 1), ("p", 3), ("d", 5)]:
        component = sum(
            np.loadtxt(f"system.PDOS.Gaussian.atom{atom}.{angular}{m}")[:, 1]
            for atom in [1, 2]
            for m in range(1, count + 1)
        )
        ax.plot(data[:, 0], component, label=f"Si {angular} (both atoms)", lw=0.9)
    ax.axvline(0, color="gray", ls="--")
    ax.set(xlabel="$E-E_F$ (eV)", ylabel="DOS (states/eV/cell)")
    ax.legend()
    fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
