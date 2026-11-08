#!/usr/bin/env python3
"""CHE free-energy steps for the four-electron OER.

The adsorption free energies in data/input.json are synthetic numbers for
checking the workflow.  They are referenced to * + H2O and * + 2H2O as
described in the note; replace them with DFT+ZPE-TS values for a real surface.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
N_E = 4
E_O2 = 4.92  # eV, 4 * 1.23 V


def steps(dG_oh: float, dG_o: float, dG_ooh: float) -> np.ndarray:
    return np.array([
        dG_oh,
        dG_o - dG_oh,
        dG_ooh - dG_o,
        E_O2 - dG_ooh,
    ])


def overpotential(dG_oh: float, dG_o: float, dG_ooh: float) -> float:
    return float(max(steps(dG_oh, dG_o, dG_ooh).max() - 1.23, 0.0))


def main() -> None:
    data = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))
    rows = []
    for item in data["catalysts"]:
        s = steps(item["dG_OH_eV"], item["dG_O_eV"], item["dG_OOH_eV"])
        rows.append({
            "name": item["name"],
            "steps_eV": [round(float(x), 3) for x in s],
            "potential_determining_step_eV": round(float(s.max()), 3),
            "overpotential_V": round(overpotential(item["dG_OH_eV"],
                                                   item["dG_O_eV"],
                                                   item["dG_OOH_eV"]), 3),
        })

    results = {
        "note": "Synthetic adsorption free energies; not a real catalyst.",
        "reference": "CHE, RHE scale, 4 e- OER",
        "catalysts": rows,
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2), constrained_layout=True)
    ax = axes[0]
    first = data["catalysts"][0]
    s0 = steps(first["dG_OH_eV"], first["dG_O_eV"], first["dG_OOH_eV"])
    for U, color, label in [(0.0, "C0", "U = 0 V"),
                            (data["potential_V"], "C1", f"U = {data['potential_V']:.2f} V")]:
        levels = np.concatenate(([0.0], np.cumsum(s0 - U)))
        ax.step(range(5), levels, where="post", color=color, lw=1.8, label=label)
        for i, level in enumerate(levels):
            ax.plot(i, level, "o", color=color, ms=4)
    ax.set_xticks(range(5))
    ax.set_xticklabels(["*", "*OH", "*O", "*OOH", "O$_2$+*"])
    ax.set_ylabel("free energy (eV)")
    ax.set_title(f"(a) OER steps, catalyst {first['name']}")
    ax.legend(frameon=False)

    ax = axes[1]
    names = [row["name"] for row in rows]
    etas = [row["overpotential_V"] for row in rows]
    ax.bar(names, etas, color=["C0", "C2", "C3"][:len(names)])
    ax.set_ylabel("overpotential $\\eta$ (V)")
    ax.set_title("(b) potential-determining step")
    for i, value in enumerate(etas):
        ax.text(i, value + 0.02, f"{value:.2f}", ha="center", fontsize=9)
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
