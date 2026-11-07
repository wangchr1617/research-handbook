"""python plot_odi.py --data odi-analysis.json --output odi.png"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    rows = json.loads(args.data.read_text())['orbitals']
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
    x = [r['index'] for r in rows]
    axes[0].bar(x, [r['native_ODI'] for r in rows], color='#236a91')
    axes[0].set_ylabel('Hirshfeld ODI (smaller = less concentrated)')
    axes[0].set_title('Atomic distribution of each orbital')
    axes[1].bar(x, [100*r['fragment_fraction'] for r in rows], color='#b45c39')
    axes[1].set_ylabel('Fraction on first water / %')
    axes[1].set_title('Fragment weight before conditional ODI')
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xlabel('Occupied spatial orbital index')
        ax.set_ylim(0, 105)
        ax.grid(axis='y', alpha=.18)
        ax.set_axisbelow(True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
