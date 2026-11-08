#!/usr/bin/env python3
"""Compute defect formation energies, transition levels, and charge neutrality.

The input energies in data/input.json are synthetic numbers for checking the
workflow.  Replace them with DFT total energies for a real material.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
K_B = 8.617333262e-5  # eV/K


def load_input() -> dict:
    with (HERE / "data" / "input.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def formation_energy(defect: dict, host: dict, mu: dict, vbm: float,
                     fermi: float, temperature: float) -> float:
    """E_f(q) = E_def - E_host - sum n_i mu_i + q (E_F + E_VBM) + E_corr."""
    delta = defect["delta_atoms"]
    stoichiometry = sum(delta.get(el, 0) * mu[el] for el in delta)
    charge_term = defect["charge"] * (fermi + vbm)
    return (defect["E_total_eV"] - host["E_total_eV"] - stoichiometry
            + charge_term + defect.get("correction_eV", 0.0))


def transition_levels(defects: list[dict], host: dict, mu: dict, vbm: float) -> list[dict]:
    """Fermi-level positions where two charge states have equal E_f."""
    levels = []
    for i, first in enumerate(defects):
        for second in defects[i + 1:]:
            if first["name"] != second["name"]:
                continue
            q1, q2 = first["charge"], second["charge"]
            if q1 == q2:
                continue
            # A(q) = E_f(q) - q * E_F; solve A1 + q1 E = A2 + q2 E.
            a1 = formation_energy(first, host, mu, vbm, 0.0, 0.0)
            a2 = formation_energy(second, host, mu, vbm, 0.0, 0.0)
            level = (a2 - a1) / (q1 - q2)
            levels.append({"defect": first["name"], "q1": q1, "q2": q2,
                           "fermi_eV": float(level)})
    return sorted(levels, key=lambda item: item["fermi_eV"])


def charge_neutrality(defects: list[dict], host: dict, mu: dict, vbm: float,
                      gap: float, temperature: float) -> tuple[float | None, np.ndarray, np.ndarray]:
    """Find E_F where the thermally averaged charge is zero."""
    grid = np.linspace(0.0, gap, 701)
    net = np.empty_like(grid)
    for index, fermi in enumerate(grid):
        energies = np.array([formation_energy(d, host, mu, vbm, fermi, temperature)
                             for d in defects])
        weights = np.exp(-(energies - energies.min()) / (K_B * temperature))
        charges = np.array([d["charge"] for d in defects])
        net[index] = float(np.sum(charges * weights) / np.sum(weights))
    root = None
    for i in range(len(grid) - 1):
        if net[i] == 0.0:
            root = float(grid[i])
            break
        if net[i] * net[i + 1] < 0.0:
            fraction = abs(net[i]) / (abs(net[i]) + abs(net[i + 1]))
            root = float(grid[i] + fraction * (grid[i + 1] - grid[i]))
            break
    return root, grid, net


def main() -> None:
    data = load_input()
    host, mu, gap = data["host"], data["chemical_potentials_eV"], data["band_gap_eV"]
    vbm, temperature = data.get("vbm_eV", 0.0), data["temperature_K"]
    defects = data["defects"]

    fermis = np.linspace(0.0, gap, 501)
    curves = {}
    for defect in defects:
        key = (defect["name"], defect["charge"])
        curves[key] = np.array([formation_energy(defect, host, mu, vbm, e, temperature)
                                for e in fermis])

    levels = transition_levels(defects, host, mu, vbm)
    fermi_eq, grid, net = charge_neutrality(defects, host, mu, vbm, gap, temperature)

    # Report formation energies at the equilibrium Fermi level (or midgap).
    report_fermi = fermi_eq if fermi_eq is not None else gap / 2.0
    table = []
    for defect in defects:
        table.append({
            "defect": defect["name"],
            "charge": defect["charge"],
            "formation_eV": round(formation_energy(defect, host, mu, vbm,
                                                    report_fermi, temperature), 4),
        })

    results = {
        "note": "Synthetic test energies; not a real material.",
        "fermi_level_eV": round(report_fermi, 4),
        "equilibrium_fermi_eV": None if fermi_eq is None else round(fermi_eq, 4),
        "transition_levels_eV": [{"defect": l["defect"], "q1": l["q1"], "q2": l["q2"],
                                  "fermi_eV": round(l["fermi_eV"], 4)} for l in levels],
        "formation_energies_eV": table,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    ax = axes[0]
    colors = plt.cm.tab10.colors
    for index, ((name, charge), values) in enumerate(curves.items()):
        ax.plot(fermis, values, color=colors[index % len(colors)], lw=1.6,
                label=f"{name}$^{{{charge:+d}}}$")
    for level in levels:
        ax.axvline(level["fermi_eV"], color="0.55", lw=0.8, ls=":")
    if fermi_eq is not None:
        ax.axvline(fermi_eq, color="k", lw=1.0, ls="--", label="charge neutrality")
    ax.set_xlim(0, gap)
    low = min(values.min() for values in curves.values())
    high = max(values.max() for values in curves.values())
    ax.set_ylim(low - 0.5, high + 0.5)
    ax.set_xlabel("Fermi level relative to VBM (eV)")
    ax.set_ylabel("Formation energy (eV)")
    ax.set_title("(a) formation energy vs Fermi level")
    ax.legend(fontsize=7, ncol=2, frameon=False)

    ax = axes[1]
    ax.plot(grid, net, color="C3")
    ax.axhline(0.0, color="0.6", lw=0.8)
    if fermi_eq is not None:
        ax.axvline(fermi_eq, color="k", lw=1.0, ls="--")
        ax.annotate(f"$E_F$ = {fermi_eq:.2f} eV", xy=(fermi_eq, 0),
                    xytext=(fermi_eq + 0.25, -0.35),
                    arrowprops={"arrowstyle": "->", "color": "k"})
    ax.set_xlim(0, gap)
    ax.set_ylim(float(net.min()) - 0.1, float(net.max()) + 0.1)
    ax.set_xlabel("Fermi level relative to VBM (eV)")
    ax.set_ylabel("mean charge per defect")
    ax.set_title("(b) charge neutrality")
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
