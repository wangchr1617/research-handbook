"""核对本例 Hirshfeld 轨道原子成分与整体/片段 ODI。

python analyze_odi.py --directory odi --log-name multiwfn.out --output odi-analysis.json
原始 orbcomp.txt 的百分比只保留三位小数；低权重片段不据此重建条件 ODI。
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np


def odi(weights):
    p = np.asarray(weights, dtype=float)
    if p.ndim != 1 or not np.isfinite(p).all() or np.any(p < 0) or p.sum() <= 0:
        raise ValueError('该 ODI 定义需要非负且总和为正的原子成分')
    p = p/p.sum()
    return float(100*np.dot(p, p))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--directory', type=Path, required=True)
    ap.add_argument('--log-name', default='multiwfn.out')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    text = (args.directory/args.log_name).read_text()
    whole_text, frag_text = text.split('ODI of the whole system:')[1].split('ODI of the fragment you defined:')
    pattern = r'Orb:\s*(\d+)\s+E\(a.u.\):\s*([-\d.]+)\s+Occ:\s*([\d.]+).*?ODI:\s*([\d.]+)'
    whole = re.findall(pattern, whole_text)
    frag = {int(i): float(v) for i, _, _, v in re.findall(pattern, frag_text)}
    composition = {}
    for block in re.split(r'\s*Orbital\s+', (args.directory/'orbcomp.txt').read_text())[1:]:
        lines = block.splitlines()
        idx = int(lines[0])
        composition[idx] = [float(v)/100 for _, v in re.findall(r'^\s*(\d+)\s+([\d.]+)\s*%', '\n'.join(lines[1:]), re.M)]
    rows = []
    for idx, energy, occupation, native in whole:
        i = int(idx)
        p = np.array(composition[i])
        if len(p) != 6 or not np.isclose(p.sum(), 1, atol=3.1e-5):
            raise ValueError('本例需要六原子且原子成分加和接近100%')
        p = p/p.sum()
        value = odi(p)
        if abs(value-float(native)) > .012:
            raise ValueError('原子成分重建 ODI 与原生日志不符')
        fraction = float(p[:3].sum())
        conditional = odi(p[:3]) if fraction >= .01 else None
        if conditional is not None and abs(conditional-frag[i]) > .2:
            raise ValueError('片段 ODI 重建偏差超过本例舍入允许范围')
        rows.append(dict(index=i, energy_Ha=float(energy), occupancy=float(occupation), rounded_atomic_fractions=p.tolist(),
                         native_ODI=float(native), reconstructed_ODI=value, effective_atoms=100/value,
                         fragment=[1, 2, 3], fragment_fraction=fraction, native_fragment_ODI=frag[i],
                         reconstructed_fragment_ODI=conditional))
    if len(rows) != 10:
        raise ValueError('本例应包含10个占据空间轨道')
    q = re.search(r'Fragment contribution:\s*([\d.]+)', text)
    norm = re.search(r'The sum of contributions before normalization\s*([\d.]+)', text)
    ngrid = re.search(r'(\d+) quadrature points are used for each atom', text)
    if q is None or ngrid is None or norm is None:
        raise ValueError('日志缺少片段权重或积分网格说明')
    data = dict(model='Fixed water dimer, PBE0/def2-SVP, same wavefunction as interaction-analysis.json', method='Hirshfeld, built-in spherical atomic densities',
                atom_centered_points_per_atom=int(ngrid[1]), formula='ODI=100*sum(p_A^2), p normalized to one',
                fragment_formula='ODI_F=100*sum((p_A/sum_F(p_A))^2)',
                composition_precision='orbcomp.txt percentages rounded to0.001%; exported fractions rescaled to sum1; fragment reconstruction omitted below1% weight',
                HOMO_fragment_percent_native=float(q[1]), HOMO_total_before_normalization_percent=float(norm[1]), orbitals=rows,
                source_sha256={name: hashlib.sha256((args.directory/name).read_bytes()).hexdigest() for name in [args.log_name, 'orbcomp.txt']})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(orbitals=len(rows), HOMO_ODI=rows[-1]['native_ODI'], HOMO_fragment_percent=float(q[1]), points_per_atom=int(ngrid[1]))))


if __name__ == '__main__':
    main()
