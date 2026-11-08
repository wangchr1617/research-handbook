#!/usr/bin/env python3
"""Phonon dispersion of a 1D diatomic chain with nearest-neighbor springs."""

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
    m1, m2, K, a = p["m1"], p["m2"], p["K_eV_per_A2"], p["a_A"]
    q = np.linspace(-np.pi / a, np.pi / a, p["n_k"])
    s = np.sin(q * a / 2.0)
    common = (m1 + m2) / (m1 * m2)
    disc = common**2 - 4.0 * s**2 / (m1 * m2)
    disc = np.maximum(disc, 0.0)
    omega2_opt = K * (common + np.sqrt(disc))
    omega2_ac = K * (common - np.sqrt(disc))

    # DOS from a dense q mesh.
    qd = np.linspace(-np.pi / a, np.pi / a, 200001)
    sd = np.sin(qd * a / 2.0)
    dd = np.maximum((m1 + m2) ** 2 / (m1 * m2) ** 2 - 4.0 * sd**2 / (m1 * m2), 0.0)
    wd = np.concatenate([
        np.sqrt(K * (common + np.sqrt(dd))),
        np.sqrt(K * (common - np.sqrt(dd))),
    ])
    hist, edges = np.histogram(wd, bins=100, density=True)
    centers = 0.5 * (edges[1:] + edges[:-1])

    results = {
        "model": "1D diatomic chain, nearest-neighbor springs",
        "m1": m1,
        "m2": m2,
        "K_eV_per_A2": K,
        "gap_lower_edge_model_units": round(float(np.sqrt(2 * K / max(m1, m2))), 4),
        "gap_upper_edge_model_units": round(float(np.sqrt(2 * K / min(m1, m2))), 4),
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(q * a / np.pi, np.sqrt(omega2_ac), color="C0", lw=1.8, label="acoustic")
    ax.plot(q * a / np.pi, np.sqrt(omega2_opt), color="C3", lw=1.8, label="optical")
    ax.set_xlabel("$q a/\\pi$")
    ax.set_ylabel("frequency $\\omega$ (arb. units)")
    ax.set_title("(a) diatomic-chain dispersion")
    ax.legend(frameon=False)

    ax = axes[1]
    ax.plot(centers, hist, color="C2", lw=1.5)
    ax.set_xlabel("frequency $\\omega$ (arb. units)")
    ax.set_ylabel("phonon DOS (arb. units)")
    ax.set_title("(b) phonon density of states")
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
