#!/usr/bin/env python3
"""对已有水优化轨迹做刚体对齐，生成原子索引/活动标记示例。

用法：python3 analyze.py --output-dir /tmp/geometry-review-new
依赖 NumPy、Matplotlib；输出目录必须不存在，坐标单位为 Å。
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'examples/orca/minimal/scan-and-descent'
spec = importlib.util.spec_from_file_location('trajectory', SOURCE / 'trajectory.py')
trajectory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trajectory)


def coordinates(value):
    a = np.asarray(value, dtype=float)
    if a.ndim != 2 or a.shape[1] != 3 or len(a) == 0 or not np.isfinite(a).all():
        raise ValueError('需要非空、有限的 N×3 坐标')
    return a


def rmsd(mobile, reference, weights=None):
    x, y = coordinates(mobile), coordinates(reference)
    if x.shape != y.shape:
        raise ValueError('原子数/对应关系的形状不一致')
    w = np.ones(len(x)) if weights is None else np.asarray(weights, dtype=float)
    if w.shape != (len(x),) or not np.isfinite(w).all() or np.any(w <= 0):
        raise ValueError('每个对应原子需要一个有限正权重')
    return float(np.sqrt(np.sum(w * np.sum((x-y)**2, axis=1)) / w.sum()))


def fit(mobile, reference, weights=None):
    """固定原子对应关系的加权 Kabsch；行向量约定 x@R+t。"""
    x, y = coordinates(mobile), coordinates(reference)
    rmsd(x, y, weights)
    w = np.ones(len(x)) if weights is None else np.asarray(weights, dtype=float)
    w = w / w.sum()
    cx, cy = w @ x, w @ y
    xc, yc = x-cx, y-cy
    u, singular, vt = np.linalg.svd(xc.T @ (w[:, None]*yc))
    parity = 1.0 if np.linalg.det(u @ vt) >= 0 else -1.0
    rotation = u @ np.diag([1.0, 1.0, parity]) @ vt
    translation = cy-cx @ rotation
    return rotation, translation, {
        'det_rotation': float(np.linalg.det(rotation)),
        'mobile_centered_rank': int(np.linalg.matrix_rank(xc)),
        'reference_centered_rank': int(np.linalg.matrix_rank(yc)),
        'covariance_singular_values_A2': singular.tolist(),
    }


def write_xyz(path, frames, comments, symbols):
    lines = []
    for xyz, comment in zip(frames, comments):
        lines.extend([str(len(symbols)), comment])
        lines.extend(f'{s} {r[0]:.10f} {r[1]:.10f} {r[2]:.10f}' for s, r in zip(symbols, xyz))
    path.write_text('\n'.join(lines)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True, help='新输出目录')
    args = parser.parse_args()
    frames = trajectory.read_xyz(SOURCE / 'optimization.xyz', 'angstrom', 'orca')
    reference = frames[0]['xyz_angstrom']
    transformed, aligned, rows, comments = [], [], [], []
    for i, frame in enumerate(frames):
        x = frame['xyz_angstrom']
        # 人工加入显示坐标系变化，不改变原子的内部几何或身份。
        a = (i % 3)*np.pi/2
        rotation = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
        mobile = x @ rotation + np.array([i*0.45, (-1)**i*0.7, i*0.2])
        r, t, diagnostics = fit(mobile, reference)
        result = mobile @ r+t
        transformed.append(mobile)
        aligned.append(result)
        rows.append({'frame_1based': i+1, 'energy_Ha': frame['energy_Ha'],
                     'raw_RMSD_A': rmsd(mobile, reference),
                     'fitted_RMSD_A': rmsd(result, reference),
                     'native_fitted_RMSD_A': rmsd(x @ fit(x, reference)[0]+fit(x, reference)[1], reference),
                     **diagnostics})
        comments.append(f"Derived display transform; source_frame={i+1}; energy_Ha={frame['energy_Ha']}; unit=angstrom")

    shell = ROOT / 'examples/solvent-shell'
    packing = trajectory.read_xyz(shell / 'packed-191917.xyz', 'angstrom')[0]
    shell_info = json.loads((shell / 'analysis.json').read_text())
    selection = next(s for s in shell_info['packings'][0]['selections'] if s['cutoff_Angstrom'] == 4)
    active = set(selection['selected_atom_indices_0based']) - set(range(5))
    assert len(packing['symbols']) == 197 and len(active) == 15
    flags = [0 if i in active else -1 for i in range(197)]
    # 这里的分子序号依据指定输入的 CH4 + 64 H2O 顺序；不用于猜测任意拓扑。
    mapping = [{'index0': i, 'index1': i+1, 'element': symbol,
                'molecule_id': 0 if i < 5 else 1+(i-5)//3, 'optflag': flags[i]}
               for i, symbol in enumerate(packing['symbols'])]

    # 非共面、固定标签的数学点集，用于说明反射不能混入刚体旋转。
    toy = np.array([[0., 0., 0.], [1., 0., 0.], [0., 2., 0.], [0., 0., 3.]])
    mirror = toy * np.array([-1, 1, 1])
    mr, mt, md = fit(mirror, toy)
    report = {'coordinate_unit': 'angstrom',
              'model': 'Six native RHF/def2-SVP water optimization frames with artificial display rotations/translations; not dynamics or native Gaussian output.',
              'mapping': 'Input order preserved; all three atoms fit/report; unit weights; first frame reference; no permutation search.',
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [SOURCE/'optimization.xyz', shell/'packed-191917.xyz', shell/'analysis.json']},
              'frames': rows,
              'mirror_toy': {'definition': 'Four labeled mathematical points; not a computed molecular structure.',
                             'proper_fit_RMSD_A': rmsd(mirror @ mr+mt, toy), **md},
              'flag_example': {'atoms': 197, 'active_atoms': len(active), 'fixed_atoms': 197-len(active),
                               'selection_cutoff_A': 4.0, 'active_atom_indices_0based': sorted(active),
                               'meaning': 'Whole nearby water molecules active, central methane and remaining waters fixed; coordinate fragment only, no MM parameters or Gaussian job.'}}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    out = args.output_dir
    write_xyz(out/'reoriented.xyz', transformed, comments, frames[0]['symbols'])
    write_xyz(out/'aligned.xyz', aligned, comments, frames[0]['symbols'])
    fields = ['frame_1based', 'energy_Ha', 'raw_RMSD_A', 'fitted_RMSD_A', 'native_fitted_RMSD_A', 'det_rotation', 'mobile_centered_rank', 'reference_centered_rank']
    with (out/'rmsd.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    with (out/'atom-map.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(mapping[0]))
        writer.writeheader()
        writer.writerows(mapping)
    fragment = [f'{s} {flags[i]} {r[0]:.6f} {r[1]:.6f} {r[2]:.6f}'
                for i, (s, r) in enumerate(zip(packing['symbols'], packing['xyz_angstrom']))]
    (out/'coordinate-fragment.txt').write_text('\n'.join(fragment)+'\n')
    (out/'analysis.json').write_text(json.dumps(report, indent=2)+'\n')
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), constrained_layout=True)
    number = [r['frame_1based'] for r in rows]
    axes[0].plot(number, [r['raw_RMSD_A'] for r in rows], 'o-', label='Raw display coordinates')
    axes[0].plot(number, [r['fitted_RMSD_A'] for r in rows], 's-', label='After proper rigid fit')
    axes[0].set(ylabel='RMSD relative to frame 1 (Å)', xlabel='Optimization frame')
    axes[0].legend(fontsize=8)
    axes[1].plot(number, [r['fitted_RMSD_A'] for r in rows], 's-', label='Display-transformed input')
    axes[1].plot(number, [r['native_fitted_RMSD_A'] for r in rows], 'x--', label='Native input')
    axes[1].set(ylabel='Fitted RMSD (Å)', xlabel='Optimization frame')
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=.25)
    fig.savefig(out/'rmsd.png', dpi=160, metadata={'Software': 'geometry-review/analyze.py'})
    plt.close(fig)
    print(json.dumps({'frames': len(rows), 'active_atoms': len(active), 'mirror_proper_RMSD_A': report['mirror_toy']['proper_fit_RMSD_A']}))


if __name__ == '__main__':
    main()
