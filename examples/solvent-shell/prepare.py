"""生成 CH4 水球 Packmol 输入及分子清单；python prepare.py --work-root NEW。"""
import argparse
import json
import math
from pathlib import Path
import shlex

HERE = Path(__file__).resolve().parent


def xyz_text(labels, coordinates, comment):
    return '\n'.join([str(len(labels)), comment]+[label+' '+' '.join(f'{v:.10f}' for v in row) for label, row in zip(labels, coordinates)])+'\n'


def prepare(root):
    cfg = json.loads((HERE/'protocol.json').read_text())
    root.mkdir(parents=True, exist_ok=False)
    h = cfg['CH_angstrom']/math.sqrt(3)
    methane = [[0., 0., 0.], [h, h, h], [h, -h, -h], [-h, h, -h], [-h, -h, h]]
    angle = math.radians(cfg['HOH_degree']/2); bond = cfg['OH_angstrom']
    water = [[0., 0., 0.], [bond*math.sin(angle), 0., bond*math.cos(angle)], [-bond*math.sin(angle), 0., bond*math.cos(angle)]]
    methane_text = xyz_text(['C']+['H']*4, methane, 'CH4; angstrom')
    water_text = xyz_text(['O', 'H', 'H'], water, 'H2O; angstrom')
    manifest = [{'molecule_id': 0, 'kind': 'solute', 'atom_indices_0based': list(range(5)), 'elements': ['C']+['H']*4}]
    for j in range(cfg['water_molecules']):
        manifest.append({'molecule_id': j+1, 'kind': 'water', 'atom_indices_0based': list(range(5+3*j, 8+3*j)), 'elements': ['O', 'H', 'H']})
    script = ['#!/usr/bin/env bash', 'set -euo pipefail', 'cd -- "$(dirname -- "$0")"', ': "${PACKMOL_EXEC:?请设置 Packmol 可执行文件绝对路径}"']
    for seed in cfg['seeds']:
        p = root/f'seed-{seed}'; p.mkdir()
        (p/'solute.xyz').write_text(methane_text); (p/'water.xyz').write_text(water_text)
        text = f'''tolerance {cfg['intermolecular_tolerance_angstrom']:g}
filetype xyz
output packed.xyz
seed {seed}
precision {cfg['packing_precision']:g}

structure solute.xyz
  number 1
  center
  fixed 0. 0. 0. 0. 0. 0.
end structure

structure water.xyz
  number {cfg['water_molecules']}
  inside sphere 0. 0. 0. {cfg['sphere_radius_angstrom']:g}
end structure
'''
        (p/'packmol.inp').write_text(text)
        (p/'molecules.json').write_text(json.dumps(manifest, indent=2)+'\n')
        script.append(f'(cd {shlex.quote(p.name)} && "$PACKMOL_EXEC" < packmol.inp > packmol.out 2>&1 && '
                      "grep -q 'Success!' packmol.out)")
    (root/'run.sh').write_text('\n'.join(script)+'\n')
    return cfg


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, required=True)
    args = parser.parse_args(); prepare(args.work_root)
