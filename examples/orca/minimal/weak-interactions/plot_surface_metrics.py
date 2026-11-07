"""从科学记录重绘阈值/筛选敏感性：python plot_surface_metrics.py --output metrics.png。"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data',type=Path,default=Path(__file__).with_name('surface-metrics.json'))
    ap.add_argument('--output',type=Path,default=Path('surface-metrics.png'))
    args=ap.parse_args();d=json.loads(args.data.read_text())
    fig,axes=plt.subplots(1,3,figsize=(12,3.7),layout='constrained')
    for key,label,marker in [('thresholds_fine','0.20 Bohr','o'),('thresholds_coarse','0.25 Bohr','s')]:
        rows=d[key]
        axes[0].plot([r['level'] for r in rows],[r['area_A2'] for r in rows],marker=marker,label=label)
        axes[1].plot([r['level'] for r in rows],[r['volume_A3'] for r in rows],marker=marker,label=label)
    axes[0].set(xlabel='IGMH isovalue (a.u.)',ylabel='Closed surface area (Angstrom^2)')
    axes[1].set(xlabel='IGMH isovalue (a.u.)',ylabel='Enclosed volume (Angstrom^3)')
    rows=d['grid_screening'];scale=[r['factor'] for r in rows]
    axes[2].plot(scale,[r['retained_grid_fraction']*100 for r in rows],marker='o',label='Grid points kept')
    axes[2].plot(scale,[r['retained_integral_fraction']*100 for r in rows],marker='s',label='Integral retained')
    axes[2].set(xlabel='Radius scale factor',ylabel='Fraction of full field (%)',ylim=(0,105))
    for ax in axes:
        ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.suptitle('Water dimer | same fixed geometry and IGMH field | finite box',fontsize=12)
    fig.savefig(args.output,dpi=180);plt.close(fig)


if __name__=='__main__':
    main()
