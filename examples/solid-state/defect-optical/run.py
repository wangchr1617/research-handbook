#!/usr/bin/env python3
"""Configuration-coordinate model for a localized defect transition."""

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
    E0, S, hw, k = p["E0_eV"], p["S"], p["hbar_omega_eV"], p["k_eV_per_A2"]
    Q0 = np.sqrt(2.0 * S * hw / k)
    Q = np.linspace(0.0, p["Q_max_A"], 400)

    ground = 0.5 * k * Q**2
    excited = E0 + 0.5 * k * (Q - Q0) ** 2
    E_abs = E0 + 0.5 * k * Q0**2
    E_em = E0 - 0.5 * k * Q0**2
    stokes = E_abs - E_em

    results = {
        "model": "two harmonic parabolas with Huang-Rhys factor S",
        "E0_eV": E0,
        "S": S,
        "hbar_omega_eV": hw,
        "Q0_A": round(float(Q0), 4),
        "absorption_eV": round(float(E_abs), 4),
        "emission_eV": round(float(E_em), 4),
        "Stokes_shift_eV": round(float(stokes), 4),
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(6.4, 4.4), constrained_layout=True)
    ax.plot(Q, ground, color="C0", lw=1.8, label="ground state")
    ax.plot(Q, excited, color="C3", lw=1.8, label="excited state")
    ax.annotate("", xy=(0.0, E_abs), xytext=(0.0, 0.0),
                arrowprops={"arrowstyle": "->", "color": "C3", "lw": 1.2})
    ax.annotate("absorption", xy=(0.06, 0.55 * E_abs), fontsize=8, color="C3")
    ax.annotate("", xy=(Q0, 0.5 * k * Q0**2), xytext=(Q0, E0),
                arrowprops={"arrowstyle": "->", "color": "C0", "lw": 1.2})
    ax.annotate("emission", xy=(Q0 + 0.03, 0.55 * (E0 + ground[np.argmin(abs(Q - Q0))])),
                fontsize=8, color="C0")
    ax.set_xlabel("configuration coordinate $Q$ (Å)")
    ax.set_ylabel("energy (eV)")
    ax.set_title("configuration-coordinate diagram")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
