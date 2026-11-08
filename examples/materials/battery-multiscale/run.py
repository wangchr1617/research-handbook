#!/usr/bin/env python3
"""Two-dimensional kinetic Monte Carlo for tracer diffusion.

Hop barriers are inputs (for example from DFT/NEB); this script shows how a
barrier turns into an Arrhenius diffusivity.  It is a minimal bridge, not a
full battery kMC model.
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


def run_temperature(temperature: float, data: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    nu = data["attempt_frequency_s"]
    rates = np.array([
        nu * np.exp(-data["barrier_x_eV"] / (K_B * temperature)),
        nu * np.exp(-data["barrier_x_eV"] / (K_B * temperature)),
        nu * np.exp(-data["barrier_y_eV"] / (K_B * temperature)),
        nu * np.exp(-data["barrier_y_eV"] / (K_B * temperature)),
    ])
    total_rate = float(rates.sum())
    steps = int(data["steps"])
    sample_every = max(1, steps // int(data["samples"]))
    a = data["lattice_constant_A"]

    x = y = 0.0          # unwrapped displacement in units of a
    time = 0.0
    times, msd = [], []
    for step in range(1, steps + 1):
        time += -np.log(rng.random()) / total_rate
        direction = int(np.searchsorted(np.cumsum(rates), rng.random() * total_rate))
        if direction == 0:
            x += 1.0
        elif direction == 1:
            x -= 1.0
        elif direction == 2:
            y += 1.0
        else:
            y -= 1.0
        if step % sample_every == 0:
            times.append(time)
            msd.append((x * x + y * y) * a * a)

    times = np.array(times)
    msd = np.array(msd)
    # Use the late-time plateau of MSD/(4t); a single random walk is too noisy
    # for a two-point slope.  A^2 -> m^2.
    late = max(1, len(times) // 4)
    diffusivity_m2_s = float(np.mean(msd[-late:] / (4.0 * times[-late:])) * 1e-20)
    return {
        "temperature_K": temperature,
        "diffusivity_m2_s": diffusivity_m2_s,
        "times_s": times.tolist(),
        "msd_A2": msd.tolist(),
    }


def main() -> None:
    data = json.loads((HERE / "data" / "input.json").read_text(encoding="utf-8"))
    # Average several independent tracers; a single walk has large fluctuations.
    runs = []
    all_samples = []
    for i, T in enumerate(data["temperatures_K"]):
        samples = [run_temperature(T, data, data["seed"] + 1000 * i + j)
                   for j in range(int(data["tracers"]))]
        all_samples.append(samples)
        d_values = np.array([s["diffusivity_m2_s"] for s in samples])
        runs.append({
            "temperature_K": T,
            "diffusivity_m2_s": float(np.median(d_values)),
            "diffusivity_std_m2_s": float(np.std(d_values, ddof=1)),
            "times_s": samples[0]["times_s"],
            "msd_A2": samples[0]["msd_A2"],
        })

    temperatures = np.array([r["temperature_K"] for r in runs])
    diffusivities = np.array([r["diffusivity_m2_s"] for r in runs])
    arr_slope, arr_intercept = np.polyfit(1.0 / temperatures, np.log(diffusivities), 1)
    activation_eV = float(-arr_slope * K_B)
    prefactor = float(np.exp(arr_intercept))

    results = {
        "note": "Minimal 2D kMC; barriers are illustrative inputs.",
        "barriers_eV": {"x": data["barrier_x_eV"], "y": data["barrier_y_eV"]},
        "arrhenius_fit": {
            "activation_eV": round(activation_eV, 4),
            "prefactor_m2_s": prefactor,
        },
        "runs": [
            {"temperature_K": r["temperature_K"],
             "diffusivity_m2_s": r["diffusivity_m2_s"],
             "diffusivity_std_m2_s": r["diffusivity_std_m2_s"]}
            for r in runs
        ],
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), constrained_layout=True)
    ax = axes[0]
    chosen_index = len(runs) // 2
    chosen = runs[chosen_index]
    samples = all_samples[chosen_index]
    times_matrix = np.array([s["times_s"] for s in samples])
    msd_matrix = np.array([s["msd_A2"] for s in samples])
    time_mean = times_matrix.mean(axis=0)
    msd_mean = np.median(msd_matrix, axis=0)
    ax.plot(time_mean * 1e6, msd_mean, "o", ms=3, color="C0",
            label=f"T = {chosen['temperature_K']} K, {len(samples)} tracers")
    ax.plot(time_mean * 1e6, 4.0 * chosen["diffusivity_m2_s"] * 1e20 * time_mean,
            "-", color="C3", lw=1.5, label="fit through origin")
    ax.set_xlabel("time (µs)")
    ax.set_ylabel("MSD (Å$^2$)")
    ax.set_title("(a) median squared displacement")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    n_tracers = float(data["tracers"])
    yerr = np.array([r["diffusivity_std_m2_s"] / np.sqrt(n_tracers)
                     / (r["diffusivity_m2_s"] * np.log(10.0)) for r in runs])
    ax.errorbar(1000.0 / temperatures, np.log10(diffusivities), yerr=yerr,
                fmt="o", color="C2", capsize=3)
    fit_x = np.linspace((1000.0 / temperatures).min(), (1000.0 / temperatures).max(), 50)
    ax.plot(fit_x, (arr_slope * (fit_x / 1000.0) + arr_intercept) / np.log(10.0),
            "-", color="0.4")
    ax.set_xlabel("1000 / T (K$^{-1}$)")
    ax.set_ylabel("log$_{10}$ D (m$^2$/s)")
    ax.set_title("(b) Arrhenius plot")
    ax.annotate(f"$E_a$ = {activation_eV:.2f} eV", xy=(0.05, 0.1),
                xycoords="axes fraction", fontsize=9)
    fig.savefig(HERE / "result.png", dpi=180)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
