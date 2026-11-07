"""从 average-data.npz 重绘三个人工水构型的局部平均场与波动截面。

用法：python plot.py --data average-data.npz --output average.png
坐标单位Å；δg单位e/Bohr^4；TFI只显示平均δg≥0.003的点。
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = np.load(args.data)
    origin, vectors = data['origin_Bohr'], data['vectors_Bohr']
    if not np.allclose(vectors, np.diag(np.diag(vectors))) or np.any(np.diag(vectors) <= 0):
        raise ValueError('本图仅支持正向正交网格')
    mean, geometry, std, tfi = (data[key] for key in ['mean', 'mean_geometry', 'std', 'tfi'])
    z = int(data['z_index'])
    x = (origin[0]+np.arange(mean.shape[0])*vectors[0, 0])*.529177210903
    y = (origin[1]+np.arange(mean.shape[1])*vectors[1, 1])*.529177210903
    fields = [mean, mean-geometry, std, np.where(mean >= .003, tfi, np.nan)]
    titles = ['Mean instantaneous delta-g', 'Mean minus mean-geometry field',
              'Population standard deviation', 'TFI = std / mean (mean >= 0.003)']
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    for i, (ax, field, title) in enumerate(zip(axes.flat, fields, titles)):
        options = dict(cmap='viridis', vmin=0)
        if i == 1:
            limit = np.max(np.abs(field[:, :, z]))
            options = dict(cmap='RdBu_r', vmin=-limit, vmax=limit)
        artist = ax.pcolormesh(x, y, field[:, :, z].T, shading='nearest', **options)
        ax.set(title=title, xlabel='x (Å)', ylabel='y (Å)', aspect='equal')
        fig.colorbar(artist, ax=ax, label='dimensionless' if i == 3 else 'e / Bohr⁴')
    slice_z = (origin[2]+z*vectors[2, 2])*.529177210903
    fig.suptitle(f'Three constructed water snapshots; local slice z = {slice_z:.3f} Å\n'
                 'First water fixed; second water shifted by 0, +0.3, -0.3 Å in y')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
