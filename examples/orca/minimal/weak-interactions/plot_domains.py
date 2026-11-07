"""从 domain-analysis.json 和 domain-plot-data.npz 重绘三种量化示例。

python plot_domains.py --data-dir . --output domain-metrics.png
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-dir', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    data = json.loads((args.data_dir/'domain-analysis.json').read_text())
    points = np.load(args.data_dir/'domain-plot-data.npz')
    fig, axes = plt.subplots(1, 3, figsize=(13.4, 3.8), constrained_layout=True)
    ax = axes[0]
    for key, c in [('coarse', '#b45c39'), ('fine', '#236a91')]:
        # 此模型的 H2···O4 区域中心位于 x≈1.6 Å；不绑定域号。
        row = min(data['IRI'][key]['domains'], key=lambda r: np.linalg.norm(np.array(r['centroid_A'])-np.array([1.65, 0, 0])))
        h = data['IRI'][key]['vectors_Bohr'][0][0]
        ax.bar(f'{h:.2f} Bohr', row['q_total_e']*1000, color=c)
        ax.text(f'{h:.2f} Bohr', row['q_total_e']*1000+.05, f"{row['points']} nodes", ha='center', fontsize=9)
    ax.set_ylabel('Electrons in selected IRI domain (×0.001 e)')
    ax.set_ylim(0, 4.1)
    ax.set_title('IRI < 1: grid sensitivity')
    ax = axes[1]
    rows = data['orbital']['meshes']
    ax.plot([x['level'] for x in rows], [x['volume_A3'] for x in rows], 'o-', color='#236a91')
    ax.set_xlabel(r'Orbital amplitude threshold / Bohr$^{-3/2}$')
    ax.set_ylabel(r'Enclosed volume / Å$^3$')
    ax.set_title('HOMO: threshold dependence')
    ax = axes[2]
    xy = points['di_de_A']
    ax.scatter(xy[:, 0], xy[:, 1], s=3, color='#236a91', alpha=.55, linewidths=0)
    ax.set_xlabel(r'$d_i$ / Å')
    ax.set_ylabel(r'$d_e$ / Å')
    ax.set_aspect('equal')
    ax.set_title('Open HS: finite-box fingerprint')
    for ax in axes[:2]:
        ax.grid(axis='y', alpha=.18)
        ax.set_axisbelow(True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
