#!/usr/bin/env python3
"""Constant-charge vs constant-potential energetics for a redox step.

E(Q) is approximated by a quadratic with a capacitance C.  The Legendre
transform Omega(U) = min_Q [E(Q) - Q U] shows how the equilibrium charge and
energy respond to electrode potential.  The numbers are synthetic.
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
    data = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))
    e0 = data["E0_eV"]
    a = data["a_eV_per_e"]
    u = np.linspace(*data["U_range_V"], 200)

    curves = {}
    for name, capacitance in data["capacitance_e_per_V"].items():
        b = 1.0 / capacitance  # eV per e^2
        q_star = (u - a) / b
        omega = e0 - (u - a) ** 2 / (2.0 * b)
        curves[name] = {"capacitance": capacitance, "q_star": q_star, "omega": omega}

    results = {
        "note": "Synthetic quadratic E(Q); not a real DFT dataset.",
        "model": "E(Q)=E0+aQ+0.5*Q^2/C; Omega(U)=min_Q[E(Q)-QU]",
        "curves": {
            name: {
                "capacitance_e_per_V": c["capacitance"],
                "omega_at_U_1V_eV": round(float(np.interp(1.0, u, c["omega"])), 4),
                "charge_at_U_1V_e": round(float(np.interp(1.0, u, c["q_star"])), 4),
            }
            for name, c in curves.items()
        },
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    for name, c in curves.items():
        b = 1.0 / c["capacitance"]
        q = np.linspace(-0.4, 0.6, 200)
        energy = e0 + a * q + 0.5 * b * q**2
        ax.plot(q, energy, lw=1.8, label=f"{name} (C={c['capacitance']:.2f} e/V)")
    ax.set_xlabel("cell charge Q (e)")
    ax.set_ylabel("E(Q) (eV)")
    ax.set_title("(a) constant-charge energy")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    for name, c in curves.items():
        ax.plot(u, c["omega"], lw=1.8, label=name)
    ax.set_xlabel("electrode potential U (V)")
    ax.set_ylabel(r"$\Omega(U)$ (eV)")
    ax.set_title("(b) constant-potential energy")
    ax.legend(frameon=False, fontsize=8)
    ax.axvline(0.0, color="0.5", lw=0.8, ls=":")
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
