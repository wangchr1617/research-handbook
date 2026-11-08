#!/usr/bin/env python3
"""Lower convex hull and voltage steps for a pseudo-binary Li_xM series.

The energies in data/input.json are synthetic numbers for checking the
workflow, not a real phase diagram.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def lower_hull(points: np.ndarray) -> list[int]:
    """Monotone chain for the lower convex hull, sorted by composition."""
    order = np.argsort(points[:, 0])
    hull: list[int] = []
    for index in order:
        while len(hull) >= 2:
            a, b = points[hull[-2]], points[hull[-1]]
            c = points[index]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 0:
                hull.pop()
            else:
                break
        hull.append(int(index))
    return hull


def main() -> None:
    data = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))
    points = np.array([[p["x_Li"], p["energy_eV_per_host"]] for p in data["points"]])
    hull = lower_hull(points)
    end_energy = np.interp(points[:, 0], points[[0, -1], 0], points[[0, -1], 1])
    formation = points[:, 1] - end_energy

    segments = []
    for left, right in zip(hull[:-1], hull[1:]):
        x1, e1 = points[left]
        x2, e2 = points[right]
        slope = (e2 - e1) / (x2 - x1)
        segments.append({
            "x_start": float(x1),
            "x_end": float(x2),
            "voltage_V": round(float(-slope), 4),
        })

    results = {
        "note": "Synthetic test energies; not a real phase diagram.",
        "reference_state": data["reference_state"],
        "stable_phases_x_Li": [round(float(points[i, 0]), 4) for i in hull],
        "stable_phases_energy_eV_per_host": [round(float(points[i, 1]), 4) for i in hull],
        "voltage_steps": segments,
        "formation_energy_eV_per_host": [
            {"x_Li": round(float(x), 4), "formation_eV_per_host": round(float(f), 4)}
            for x, f in zip(points[:, 0], formation)
        ],
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(points[:, 0], points[:, 1], "o", ms=5, color="0.35", label="candidate structures")
    ax.plot(points[hull, 0], points[hull, 1], "-o", color="C0", lw=1.8,
            label="lower convex hull")
    ax.set_xlabel("x in Li$_x$M")
    ax.set_ylabel("Li-referenced energy per host unit (eV)")
    ax.set_title("(a) convex hull")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    for segment in segments:
        ax.hlines(segment["voltage_V"], segment["x_start"], segment["x_end"],
                  color="C3", lw=2.2)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, max(s["voltage_V"] for s in segments) * 1.25)
    ax.set_xlabel("x in Li$_x$M")
    ax.set_ylabel("voltage vs Li metal (V)")
    ax.set_title("(b) voltage steps from hull slopes")
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
