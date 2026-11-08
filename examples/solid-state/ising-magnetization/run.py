#!/usr/bin/env python3
"""Metropolis Monte Carlo for the 2D Ising model on a square lattice."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
TC_EXACT = 2.0 / np.log(1.0 + np.sqrt(2.0))


def sweep(spins: np.ndarray, beta: float, rng: np.random.Generator, J: float) -> None:
    """One checkerboard sweep; each spin is visited once."""
    L = spins.shape[0]
    for parity in (0, 1):
        idx = (np.indices((L, L)).sum(axis=0) % 2) == parity
        nb = (np.roll(spins, 1, 0) + np.roll(spins, -1, 0)
              + np.roll(spins, 1, 1) + np.roll(spins, -1, 1))
        dE = 2.0 * J * spins * nb
        accept = (dE <= 0) | (rng.random((L, L)) < np.exp(-beta * np.minimum(dE, 50.0)))
        spins[idx & accept] *= -1


def main() -> None:
    p = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))
    L, J, temps = p["L"], p["J"], p["temperatures"]
    n_burn, n_sweeps = p["n_burn"], p["n_sweeps"]
    rng = np.random.default_rng(p["seed"])

    rows = []
    for T in temps:
        beta = 1.0 / T
        spins = rng.choice([-1, 1], size=(L, L))
        for _ in range(n_burn):
            sweep(spins, beta, rng, J)
        mags, energies = [], []
        for _ in range(n_sweeps):
            sweep(spins, beta, rng, J)
            mags.append(abs(spins.mean()))
            energies.append(-J * (spins * (np.roll(spins, 1, 0) + np.roll(spins, 1, 1))).sum())
        mags = np.array(mags)
        rows.append({
            "T": float(T),
            "magnetization": float(mags.mean()),
            "susceptibility": float(L * L / T * (mags**2).mean() - (L * L / T) * mags.mean()**2),
            "energy_per_spin": float(np.mean(energies) / (L * L)),
        })

    peak = max(rows, key=lambda r: r["susceptibility"])
    results = {
        "model": "2D Ising, square lattice, periodic boundaries",
        "L": L,
        "J": J,
        "Tc_exact_J_over_kB": round(float(TC_EXACT), 4),
        "Tc_from_chi_peak": round(float(peak["T"]), 4),
        "points": rows,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    Ts = np.array([r["T"] for r in rows])
    M = np.array([r["magnetization"] for r in rows])
    chi = np.array([r["susceptibility"] for r in rows])

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(Ts, M, "o-", color="C0")
    ax.axvline(TC_EXACT, color="0.4", ls="--", lw=1, label=f"exact $T_c$ = {TC_EXACT:.3f}")
    ax.set_xlabel("temperature $T$ ($J/k_B$)")
    ax.set_ylabel("$\\langle |m| \\rangle$")
    ax.set_title("(a) magnetization")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    ax.plot(Ts, chi, "o-", color="C3")
    ax.axvline(TC_EXACT, color="0.4", ls="--", lw=1)
    ax.set_xlabel("temperature $T$ ($J/k_B$)")
    ax.set_ylabel("susceptibility $\\chi$ (arb. units)")
    ax.set_title("(b) susceptibility peak")
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
