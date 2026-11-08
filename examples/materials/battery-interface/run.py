#!/usr/bin/env python3
"""Work of adhesion and electron tunneling through an SEI layer.

The slab/interface energies in data/input.json are synthetic numbers used to
check the workflow; they are not a real Li|SEI interface.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
EV_A2_TO_J_M2 = 16.02176634
M_E = 9.1093837015e-31
HBAR = 1.054571817e-34
E_CHARGE = 1.602176634e-19


def main() -> None:
    data = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))

    rows = []
    for item in data["interfaces"]:
        work = (item["E_slab_a_eV"] + item["E_slab_b_eV"] - item["E_interface_eV"])
        work_per_area = work / item["area_A2"]
        rows.append({
            "interface": item["name"],
            "work_of_adhesion_eV_per_A2": round(work_per_area, 4),
            "work_of_adhesion_J_per_m2": round(work_per_area * EV_A2_TO_J_M2, 3),
        })

    tunneling = data["tunneling"]
    barrier_j = tunneling["barrier_eV"] * E_CHARGE
    mass = tunneling["effective_mass_m_e"] * M_E
    kappa = np.sqrt(2.0 * mass * barrier_j) / HBAR  # m^-1
    thickness_m = np.array(tunneling["thickness_nm"]) * 1e-9
    transmission = np.exp(-2.0 * kappa * thickness_m)
    decay_length_nm = 1e9 / (2.0 * kappa)

    results = {
        "note": "Synthetic test energies; not a real interface.",
        "interfaces": rows,
        "tunneling": {
            "barrier_eV": tunneling["barrier_eV"],
            "kappa_per_nm": round(float(kappa / 1e9), 4),
            "decay_length_nm": round(float(decay_length_nm), 4),
            "transmission": [
                {"thickness_nm": float(t), "transmission": float(tr)}
                for t, tr in zip(tunneling["thickness_nm"], transmission)
            ],
        },
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    names = [row["interface"] for row in rows]
    values = [row["work_of_adhesion_J_per_m2"] for row in rows]
    colors = ["C0", "C2", "C3"]
    ax.bar(range(len(names)), values, color=colors[:len(names)])
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15, ha="right", fontsize=8)
    ax.set_ylabel("work of adhesion (J/m$^2$)")
    ax.set_title("(a) interface adhesion")

    ax = axes[1]
    ax.semilogy(tunneling["thickness_nm"], transmission, "o-", color="C3")
    ax.set_xlabel("SEI thickness (nm)")
    ax.set_ylabel("electron transmission")
    ax.set_title("(b) tunneling through a square barrier")
    ax.grid(True, which="both", ls=":", lw=0.6, alpha=0.6)
    ax.annotate(f"decay length = {decay_length_nm:.2f} nm",
                xy=(0.5, 0.15), xycoords="axes fraction", fontsize=8)
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
