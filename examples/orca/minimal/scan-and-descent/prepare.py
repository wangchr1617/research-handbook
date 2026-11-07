"""生成水的角度扫描和下坡初始结构；python prepare.py --work-root NEW_DIRECTORY。"""
import argparse
import json
import math
from pathlib import Path
import shlex
import shutil

HERE = Path(__file__).resolve().parent


def water_xyz(angle, bond):
    a = math.radians(angle/2)
    x, z = bond*math.sin(a), bond*math.cos(a)
    return f'3\nWater angle={angle:g} degree; coordinates in angstrom\nO 0 0 0\nH {x:.12f} 0 {z:.12f}\nH {-x:.12f} 0 {z:.12f}\n'


def prepare(root):
    cfg = json.loads((HERE/'protocol.json').read_text())
    root.mkdir(parents=True, exist_ok=False)
    jobs = []
    for angle in cfg['angles_degree']:
        for method in ['rigid', 'relaxed']:
            jobs.append({'path': f'a{angle:g}/{method}', 'method': method, 'angle_degree': angle})
    jobs += [{'path': mode, 'method': mode, 'angle_degree': cfg['angles_degree'][0]} for mode in ['free', 'downhill']]
    for job in jobs:
        p = root/job['path']; p.mkdir(parents=True)
        (p/'structure.xyz').write_text(water_xyz(job['angle_degree'], cfg['initial_OH_angstrom']))
        shutil.copy2(HERE/f'{job["method"]}.inp', p/'calc.inp')
    (root/'jobs.json').write_text(json.dumps(jobs, indent=2)+'\n')
    script = ['#!/usr/bin/env bash', 'set -euo pipefail', 'cd -- "$(dirname -- "$0")"',
              ': "${ORCA_EXEC:?请设置 ORCA 驱动绝对路径}"']
    for job in jobs:
        script.append(f'(cd {shlex.quote(job["path"])} && "$ORCA_EXEC" calc.inp > calc.out 2>&1 && '
                      "grep -q 'ORCA TERMINATED NORMALLY' calc.out)")
    (root/'run.sh').write_text('\n'.join(script)+'\n')
    return jobs


def prepare_endpoint(root):
    text = (root/'downhill/calc.out').read_text()
    if 'ORCA TERMINATED NORMALLY' not in text or text.count('THE IRC HAS CONVERGED') != 1:
        raise ValueError('downhill 没有正常结束且收敛')
    folder = root/'down-end'; folder.mkdir(exist_ok=False)
    shutil.copy2(HERE/'free.inp', folder/'calc.inp')
    shutil.copy2(root/'downhill/calc_IRC_D.xyz', folder/'structure.xyz')
    return ['down-end']


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--work-root', type=Path, required=True); p.add_argument('--stage', choices=['initial', 'endpoint'], default='initial')
    a = p.parse_args(); jobs = prepare(a.work_root) if a.stage == 'initial' else prepare_endpoint(a.work_root); print(f'Prepared {len(jobs)} independent jobs.')


if __name__ == '__main__':
    main()
