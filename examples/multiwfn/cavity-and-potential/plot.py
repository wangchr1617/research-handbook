"""python examples/multiwfn/cavity-and-potential/plot.py --data cavity-potential.json --output cavity-potential.png"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    d = json.loads(args.data.read_text())
    fig, axes = plt.subplots(1, 3, figsize=(13.3, 3.8), constrained_layout=True)
    s = d['cavity_section']
    value = np.log10(np.maximum(np.array(s['density']).T, 1e-12))
    im = axes[0].pcolormesh(s['x_A'], s['y_A'], value, shading='nearest', cmap='viridis', vmin=-4, vmax=0)
    axes[0].contour(s['x_A'], s['y_A'], value, levels=[-2, np.log10(.05)], colors=['white', '#f28c28'], linewidths=1)
    axes[0].set_aspect('equal')
    axes[0].set_xlabel('x / Å'); axes[0].set_ylabel('y / Å')
    axes[0].set_title(f"Ideal C20 sites: z={s['z_A']:.3f} Å", fontsize=11)
    fig.colorbar(im, ax=axes[0], label=r'$\log_{10}(\rho_{pro}/[e\,Bohr^{-3}])$')
    for key, color in [('coarse', '#b45c39'), ('fine', '#236a91')]:
        rows = [x for x in d['cavity'][key]['thresholds'] if x['status'] == 'closed_component']
        step = d['cavity'][key]['vectors_Bohr'][0][0]
        axes[1].plot([x['cutoff_e_Bohr3'] for x in rows], [x['volume_A3'] for x in rows], 'o-', color=color, label=f'{step:.2f} Bohr grid')
    axes[1].set_xlim(0, .052); axes[1].set_ylim(0, 3.3)
    axes[1].text(.001, 2.85, 'At 0.001 / 0.005:\nno central low-density domain', fontsize=8)
    axes[1].text(.026, .45, 'At 0.05:\nconnected to exterior', fontsize=8)
    axes[1].set_xlabel(r'Density threshold / $e\,Bohr^{-3}$')
    axes[1].set_ylabel('Closed central domain volume / Å³')
    axes[1].set_title('Cavity depends on its definition', fontsize=11)
    axes[1].legend(frameon=False, fontsize=8, loc='upper right')
    for element, color in [('He', '#236a91'), ('C', '#b45c39'), ('Ar', '#587b39')]:
        row = d['uff']['curves'][element]
        axes[2].plot(d['uff']['curve_radius_A'], row['values_kcal_mol'], color=color, label=element+' probe')
        axes[2].plot(row['minimum_radius_A'], row['minimum_energy_kcal_mol'], 'o', color=color, ms=4)
    axes[2].axhline(0, color='#777777', lw=.6)
    axes[2].set_ylim(-.22, .5)
    axes[2].set_xlabel('Distance from fixed Ar / Å')
    axes[2].set_ylabel('Pair UFF energy / kcal mol⁻¹')
    axes[2].set_title('Probe-dependent pair potential', fontsize=11)
    axes[2].legend(frameon=False, fontsize=8)
    for ax in axes[1:]:
        ax.grid(alpha=.15)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
