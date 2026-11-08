#!/usr/bin/env python3
"""Stability of a single metal atom and a dimer on a support.

E_single_atom and E_dimer are total DFT energies of the same slab with one
metal atom or two metal atoms.  The numbers in data/input.json are synthetic.
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
    e_support = data["E_support_eV"]
    e_single = data["E_single_atom_eV"]
    e_dimer = data["E_dimer_eV"]
    e_bulk = data["E_bulk_per_atom_eV"]

    # Formation energy relative to the clean support and the metal reservoir.
    def e_form_single(mu: np.ndarray) -> np.ndarray:
        return e_single - e_support - mu

    def e_form_dimer_per_atom(mu: np.ndarray) -> np.ndarray:
        return (e_dimer - e_support - 2.0 * mu) / 2.0

    # 2 M@support -> M2@support + support
    dimerization = e_dimer + e_support - 2.0 * e_single

    mu = np.linspace(data["mu_min_eV"], data["mu_max_eV"], 200)
    single = e_form_single(mu)
    dimer = e_form_dimer_per_atom(mu)
    stable_mu = mu[mu <= e_bulk]
    stable_single = single[mu <= e_bulk]

    results = {
        "note": "Synthetic energies; not a real catalyst.",
        "formation_energy_single_at_mu_bulk_eV": round(float(e_form_single(np.array([e_bulk]))[0]), 4),
        "dimerization_energy_eV": round(float(dimerization), 4),
        "stable_mu_range_eV": [round(float(stable_mu.min()), 3), round(float(stable_mu.max()), 3)],
        "single_atom_stable_at_mu_bulk": bool(e_form_single(np.array([e_bulk]))[0] < 0),
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(mu, single, color="C0", lw=1.8, label="single atom")
    ax.plot(mu, dimer, color="C2", lw=1.8, label="dimer (per atom)")
    ax.axvline(e_bulk, color="0.4", ls="--", lw=1, label=r"$\mu_M = E_{\rm bulk}$")
    ax.axhline(0.0, color="0.6", lw=0.8)
    ax.fill_between(stable_mu, -5, 6, color="C0", alpha=0.06)
    ax.set_xlabel(r"$\mu_M$ (eV)")
    ax.set_ylabel("formation energy (eV per metal atom)")
    ax.set_title("(a) stability vs metal chemical potential")
    ax.set_ylim(-4, 5)
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    labels = ["binding\n(single)", "binding\n(dimer, per atom)", "dimerization"]
    values = [e_single - e_support, (e_dimer - e_support) / 2.0, dimerization]
    colors = ["C0", "C2", "C3"]
    ax.bar(labels, values, color=colors)
    ax.axhline(0.0, color="0.4", lw=0.8)
    ax.set_ylim(min(values) - 1.0, max(values) + 1.0)
    ax.set_ylabel("energy (eV)")
    ax.set_title("(b) binding and aggregation")
    for i, value in enumerate(values):
        ax.text(i, value + (0.2 if value >= 0 else -0.5), f"{value:.2f}", ha="center", fontsize=8)
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
