#!/usr/bin/env python3
"""Landau-Devonshire double well: polarization, susceptibility, hysteresis."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def free_energy(P, alpha, beta, E):
    return 0.5 * alpha * P**2 + 0.25 * beta * P**4 - E * P


def stable_polarization(alpha, beta, E, previous=None):
    roots = np.roots([beta, 0.0, alpha, -E])
    real = [float(r.real) for r in roots if abs(r.imag) < 1e-8]
    if not real:
        return 0.0
    if previous is not None:
        closest = min(real, key=lambda x: abs(x - previous))
        # Stay on the metastable branch if it is still a local minimum.
        if alpha + 3 * beta * closest**2 > 0:
            return closest
    return min(real, key=lambda x: free_energy(x, alpha, beta, E))


def main() -> None:
    p = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))
    Tc, a0, beta = p["Tc"], p["a0"], p["beta"]
    Ts = np.array(p["T_points"])
    alpha = a0 * (Ts - Tc)
    Ps = np.sqrt(np.maximum(-alpha / beta, 0.0))

    E = np.linspace(-p["E_max"], p["E_max"], p["n_E"])
    alpha_loop = a0 * (0.6 - Tc)
    up, down = [], []
    prev = -np.sqrt(max(-alpha_loop / beta, 0.0))
    for e in E:
        prev = stable_polarization(alpha_loop, beta, e, prev)
        up.append(prev)
    prev = np.sqrt(max(-alpha_loop / beta, 0.0))
    for e in E[::-1]:
        prev = stable_polarization(alpha_loop, beta, e, prev)
        down.append(prev)
    down = down[::-1]

    results = {
        "model": "Landau-Devonshire F = alpha/2 P^2 + beta/4 P^4 - E P",
        "Tc": Tc,
        "a0": a0,
        "beta": beta,
        "Ps_at_lowest_T": round(float(Ps[0]), 4),
        "coercive_field_estimate": round(float(2 / (3 * np.sqrt(3)) * (-alpha_loop) ** 1.5 / np.sqrt(beta)), 4),
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(Ts, Ps, "o-", color="C0")
    ax.axvline(Tc, color="0.4", ls="--", lw=1, label=f"$T_c$ = {Tc}")
    ax.set_xlabel("temperature (arb. units)")
    ax.set_ylabel("spontaneous polarization $P_s$")
    ax.set_title("(a) order parameter")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    ax.plot(E, up, color="C3", lw=1.8, label="increasing E")
    ax.plot(E, down, color="C0", lw=1.8, ls="--", label="decreasing E")
    ax.axhline(0, color="0.8", lw=0.8)
    ax.axvline(0, color="0.8", lw=0.8)
    ax.set_xlabel("electric field $E$ (arb. units)")
    ax.set_ylabel("polarization $P$")
    ax.set_title("(b) hysteresis loop at $T < T_c$")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
