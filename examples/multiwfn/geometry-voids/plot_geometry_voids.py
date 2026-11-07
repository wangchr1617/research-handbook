"""python plot_geometry_voids.py --data geometry-voids.json --output geometry-voids.png"""
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
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.6), constrained_layout=True)
    xyz = np.array(d['cluster']['cluster_A'])
    for mol in xyz.reshape(-1, 3, 3):
        for h in [1, 2]:
            axes[0].plot(mol[[0, h], 0], mol[[0, h], 1], color='#777777', lw=1)
    o = np.array(d['cluster']['cluster_elements']) == 'O'
    axes[0].scatter(xyz[o, 0], xyz[o, 1], c='#b45c39', s=35, zorder=3)
    axes[0].scatter(xyz[~o, 0], xyz[~o, 1], c='#236a91', s=16, zorder=3)
    axes[0].add_patch(plt.Rectangle((0, 0), 4, 4, fill=False, ls='--', color='#777777'))
    axes[0].set_title('Whole molecules across cell boundaries')
    axes[0].set_xlabel('x / Å')
    axes[0].set_ylabel('y / Å')
    axes[0].set_aspect('equal')
    rows = d['free_regions'][:2]
    labels = [f"{x['requested_spacing_A']:.2f} requested\n{x['actual_vectors_A'][0][0]:.3f} actual" for x in rows]
    axes[1].scatter(labels, [x['raw_free_volume_A3'] for x in rows], c=['#b45c39', '#236a91'], s=65, zorder=3)
    axes[1].axhline(rows[0]['analytic_sphere_free_volume_A3'], color='#555555', ls='--', label='Sphere reference')
    axes[1].set_ylim(475, 492)
    axes[1].set_ylabel('Geometric free volume / Å³')
    axes[1].set_xlabel('Grid spacing / Å')
    axes[1].set_title('One Ar in an 8 Å cubic cell')
    axes[1].legend(frameon=False, fontsize=8)
    s = d['section']
    im = axes[2].pcolormesh(s['x_A'], s['y_A'], np.array(s['smooth']).T, shading='nearest', vmin=0, vmax=1, cmap='viridis')
    axes[2].add_patch(plt.Circle((4, 4), 1.88, fill=False, color='white', ls='--', lw=1))
    axes[2].set_aspect('equal')
    axes[2].set_xlabel('x / Å')
    axes[2].set_ylabel('y / Å')
    axes[2].set_title(f"Smoothed field, z={s['z_A']:.3f} Å")
    fig.colorbar(im, ax=axes[2], label='Free-region display field')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
