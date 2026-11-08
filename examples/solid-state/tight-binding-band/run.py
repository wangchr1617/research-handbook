#!/usr/bin/env python3
"""Bands and DOS of a dimerized 1D tight-binding chain.

E(k) = +/- sqrt(t1^2 + t2^2 + 2 t1 t2 cos(k a))
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main() -> None:
    p = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))
    t1, t2, a = p["t1_eV"], p["t2_eV"], p["a_A"]
    k = np.linspace(-np.pi / a, np.pi / a, p["n_k"])
    radicand = t1**2 + t2**2 + 2 * t1 * t2 * np.cos(k * a)
    upper = np.sqrt(radicand)
    lower = -upper

    # Brillouin-zone averaged DOS from a dense k mesh.
    kd = np.linspace(-np.pi / a, np.pi / a, 200001)
    ed = np.sqrt(t1**2 + t2**2 + 2 * t1 * t2 * np.cos(kd * a))
    energies = np.concatenate([ed, -ed])
    hist, edges = np.histogram(energies, bins=120, density=True)
    centers = 0.5 * (edges[1:] + edges[:-1])

    gap = 2 * abs(t1 - t2)
    results = {
        "model": "dimerized 1D chain, two sites per cell",
        "t1_eV": t1,
        "t2_eV": t2,
        "gap_at_zone_boundary_eV": round(float(gap), 4),
        "bandwidth_eV": round(float(2 * (t1 + t2)), 4),
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(k * a / np.pi, upper, color="C0", lw=1.8, label="$E_+$")
    ax.plot(k * a / np.pi, lower, color="C0", lw=1.8, label="$E_-$")
    ax.axhline(0, color="0.8", lw=0.8)
    ax.set_xlabel("$k a/\\pi$")
    ax.set_ylabel("energy (eV)")
    ax.set_title("(a) dimerized chain bands")
    ax.legend(frameon=False)

    ax = axes[1]
    ax.plot(centers, hist, color="C3", lw=1.5)
    ax.set_xlabel("energy (eV)")
    ax.set_ylabel("DOS (arb. units)")
    ax.set_title("(b) density of states")
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
