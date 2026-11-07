"""核对普通XYZ完整帧并导出几何表；python trajectory.py INPUT --coordinate-unit angstrom --output-dir NEW。"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil

import numpy as np

BOHR_ANGSTROM = .529177210903
NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?'


def read_xyz(path, coordinate_unit, energy_format='none'):
    if coordinate_unit not in ['angstrom', 'bohr'] or energy_format not in ['none', 'orca']:
        raise ValueError('必须明确坐标单位和已知的能量注释格式')
    lines = Path(path).read_text().splitlines()
    frames = []; symbols = None; i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        if not re.fullmatch(r'\s*[1-9]\d*\s*', lines[i]):
            raise ValueError(f'第{i+1}行不是正整数原子数')
        n = int(lines[i])
        if i+n+2 > len(lines):
            raise ValueError('轨迹末帧不完整，未导出部分原子')
        comment = lines[i+1]
        rows = [line.split() for line in lines[i+2:i+2+n]]
        if any(len(row) != 4 or not re.fullmatch(r'[A-Z][a-z]?', row[0]) for row in rows):
            raise ValueError('仅接受元素符号和三列坐标组成的普通XYZ')
        current = [row[0] for row in rows]
        if symbols is not None and current != symbols:
            raise ValueError('帧间原子数、元素或顺序改变')
        symbols = current
        xyz = np.array([[float(v.replace('D', 'E').replace('d', 'e')) for v in row[1:]] for row in rows])
        if not np.isfinite(xyz).all():
            raise ValueError('XYZ中存在非有限坐标')
        if coordinate_unit == 'bohr':
            xyz *= BOHR_ANGSTROM
        energy = None
        if energy_format == 'orca':
            match = re.fullmatch(r'Coordinates from ORCA-job \S+ E\s+('+NUMBER+r')\s*', comment)
            if not match:
                raise ValueError('未找到明确的原生ORCA能量注释，不能猜测其数值或单位')
            energy = float(match[1].replace('D', 'E').replace('d', 'e'))
        payload = json.dumps({'symbols': symbols, 'xyz_angstrom': xyz.tolist()}, separators=(',', ':'))
        frames.append({'frame_1based': len(frames)+1, 'symbols': symbols.copy(),
                       'xyz_angstrom': xyz.tolist(), 'energy_Ha': energy, 'source_comment': comment,
                       'geometry_sha256': hashlib.sha256(payload.encode()).hexdigest()})
        i += n+2
    if not frames:
        raise ValueError('轨迹为空')
    return frames


def angle(xyz, a, b, c):
    u, v = xyz[a]-xyz[b], xyz[c]-xyz[b]
    norm = np.linalg.norm(u)*np.linalg.norm(v)
    if norm < 1e-14:
        raise ValueError('重合原子不能定义夹角')
    return float(np.degrees(np.arccos(np.clip(u@v/norm, -1, 1))))


def rows_for(frames, bonds=(), angles=()):
    result = []
    for frame in frames:
        xyz = np.array(frame['xyz_angstrom']); n = len(xyz)
        row = {'frame_1based': frame['frame_1based'], 'energy_Ha': frame['energy_Ha'],
               'geometry_sha256': frame['geometry_sha256']}
        for atoms in list(bonds)+list(angles):
            if any(i < 1 or i > n for i in atoms) or len(set(atoms)) != len(atoms):
                raise ValueError('几何指标使用从1开始且互不重复的有效原子编号')
        for a, b in bonds:
            row[f'bond_{a}_{b}_angstrom'] = float(np.linalg.norm(xyz[a-1]-xyz[b-1]))
        for a, b, c in angles:
            row[f'angle_{a}_{b}_{c}_degree'] = angle(xyz, a-1, b-1, c-1)
        result.append(row)
    return result


def write_csv(path, rows):
    with Path(path).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def export(path, out, unit, energy_format='none', expected_frames=None, bonds=(), angles=()):
    path, out = Path(path), Path(out)
    frames = read_xyz(path, unit, energy_format)
    if expected_frames is not None and len(frames) != expected_frames:
        raise ValueError('完整帧数与预期不符')
    rows = rows_for(frames, bonds, angles)
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(path, out/'source.xyz')
    write_csv(out/'geometry.csv', rows)
    manifest = {'source_name': path.name, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'input_coordinate_unit': unit, 'output_coordinate_unit': 'angstrom', 'energy_format': energy_format,
                'atom_symbols': frames[0]['symbols'], 'complete_frames': len(frames),
                'distinct_geometries': len({x['geometry_sha256'] for x in frames}),
                'same_element_identity_mapping': 'Requires external atom identity mapping; equal symbols alone cannot detect a permutation',
                'frames': rows}
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('input', type=Path)
    p.add_argument('--coordinate-unit', required=True, choices=['angstrom', 'bohr'])
    p.add_argument('--energy-format', choices=['none', 'orca'], default='none')
    p.add_argument('--expected-frames', type=int);p.add_argument('--output-dir', required=True, type=Path)
    p.add_argument('--bond', action='append', default=[]);p.add_argument('--angle', action='append', default=[])
    a = p.parse_args()
    bonds = [tuple(map(int, s.split(','))) for s in a.bond]
    angles = [tuple(map(int, s.split(','))) for s in a.angle]
    if any(len(v) != 2 for v in bonds) or any(len(v) != 3 for v in angles):
        p.error('--bond应为1,2；--angle应为2,1,3；编号从1开始')
    m = export(a.input, a.output_dir, a.coordinate_unit, a.energy_format, a.expected_frames, bonds, angles)
    print(json.dumps({'complete_frames': m['complete_frames'], 'atom_symbols': m['atom_symbols']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
