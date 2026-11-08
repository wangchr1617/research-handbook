#!/usr/bin/env python3
"""OER volcano from one descriptor and a linear scaling relation.

For the one-dimensional slice, dG_O = ratio * dG_OH and
dG_OOH = dG_OH + offset.  The four CHE steps are
  dG1 = dG_OH
  dG2 = dG_O - dG_OH
  dG3 = dG_OOH - dG_O
  dG4 = 4.92 - dG_OOH
The numbers are synthetic and the 2x scaling is only for illustration.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def overpotential(dg_oh, dg_o, offset):
    dg_ooh = dg_oh + offset
    steps = np.stack([dg_oh, dg_o - dg_oh, dg_ooh - dg_o, 4.92 - dg_ooh])
    return steps.max(axis=0) - 1.23


def main() -> None:
    data = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))
    dg_oh = np.linspace(*data["dG_OH_range_eV"], 400)
    offset = data["dG_OOH_offset_eV"]
    ratio = data["dG_O_ratio"]

    dg_o = ratio * dg_oh
    eta = overpotential(dg_oh, dg_o, offset)
    best = int(np.argmin(eta))

    oh_grid = np.linspace(*data["dG_OH_range_eV"], 160)
    o_grid = np.linspace(0.2, 3.0, 160)
    oh_mesh, o_mesh = np.meshgrid(oh_grid, o_grid)
    eta_map = overpotential(oh_mesh, o_mesh, offset)

    results = {
        "note": "Synthetic scaling-relation illustration; not a real DFT dataset.",
        "one_dimensional_scaling": "dG_O = ratio * dG_OH; dG_OOH = dG_OH + offset",
        "ratio": ratio,
        "min_overpotential_V": round(float(eta[best]), 4),
        "optimal_dG_OH_eV": round(float(dg_oh[best]), 4),
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(dg_oh, eta, color="C0", lw=1.8, label=r"$\Delta G_O = 2\Delta G_{OH}$")
    ax.plot(dg_oh[best], eta[best], "o", color="C3", ms=6,
            label=f"minimum: {eta[best]:.2f} V at {dg_oh[best]:.2f} eV")
    ax.set_xlabel(r"$\Delta G_{\rm OH}$ (eV)")
    ax.set_ylabel(r"OER overpotential $\eta$ (V)")
    ax.set_title("(a) one-dimensional volcano")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    image = ax.imshow(eta_map, origin="lower", aspect="auto",
                      extent=[oh_grid.min(), oh_grid.max(), o_grid.min(), o_grid.max()],
                      cmap="viridis")
    ax.plot(dg_oh, dg_o, color="w", lw=1.2, ls="--", label="slice in (a)")
    ax.set_ylim(o_grid.min(), o_grid.max())
    ax.set_xlabel(r"$\Delta G_{\rm OH}$ (eV)")
    ax.set_ylabel(r"$\Delta G_O$ (eV)")
    ax.set_title("(b) two-descriptor map")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.colorbar(image, ax=ax, label=r"$\eta$ (V)")
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
