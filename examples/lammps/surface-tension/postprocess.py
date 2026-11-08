#!/usr/bin/env python3
"""Parse the LAMMPS surface-tension run and plot the pressure-tensor estimate."""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main() -> None:
    log = (HERE / "log.surface").read_text(encoding="utf-8")
    match = re.search(r"(?m)^GAMMA_RESULT\s+(\S+)\s*$", log)
    if not match:
        raise SystemExit("GAMMA_RESULT not found in log.surface")
    gamma = float(match.group(1))

    thermo = re.search(
        r"(?m)^\s*Step\s+Temp\s+Pxx\s+Pyy\s+Pzz\s+v_gamma[^\S\n]*\n"
        r"(?P<rows>.*?)^Loop time",
        log,
        re.DOTALL,
    )
    if thermo is None:
        raise SystemExit("production thermo table not found")
    data = np.loadtxt(thermo.group("rows").splitlines(), ndmin=2)
    if data.shape[1] != 6 or data.shape[0] < 10:
        raise SystemExit("expected six thermo columns and at least ten samples")

    step, temp, pxx, pyy, pzz, inst = data.T
    blocks = np.array_split(data, 10)
    block_means = [float(block[:, -1].mean()) for block in blocks]

    results = {
        "note": "LJ liquid-vapor surface tension from the global pressure tensor; two interfaces.",
        "gamma": round(gamma, 6),
        "mean_temperature": round(float(np.mean(temp)), 6),
        "mean_pxx": round(float(np.mean(pxx)), 6),
        "mean_pyy": round(float(np.mean(pyy)), 6),
        "mean_pzz": round(float(np.mean(pzz)), 6),
        "block_means": [round(x, 6) for x in block_means],
        "n_thermo_rows": int(len(step)),
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(step, inst, lw=0.7, color="C0", alpha=0.8)
    ax.axhline(gamma, color="C3", lw=1.2, label=f"mean = {gamma:.3f}")
    ax.set_xlabel("step")
    ax.set_ylabel(r"$\gamma$ ($\epsilon/\sigma^2$)")
    ax.set_title("(a) instantaneous surface tension")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    centers = [float(block[:, 0].mean()) for block in blocks]
    ax.plot(centers, block_means, "o-", color="C2")
    ax.axhline(gamma, color="C3", lw=1.2, label="full-run mean")
    ax.set_xlabel("step")
    ax.set_ylabel(r"block mean $\gamma$ ($\epsilon/\sigma^2$)")
    ax.set_title("(b) block averages")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
