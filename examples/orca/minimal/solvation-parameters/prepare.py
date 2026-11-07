"""生成 Br− 半径对照和 H2O 电荷/溶剂输入；python prepare.py --work-root NEW。"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil

HERE = Path(__file__).resolve().parent


def script(root, jobs, name):
    lines = ['#!/usr/bin/env bash', 'set -euo pipefail', 'cd -- "$(dirname -- "$0")"',
             ': "${ORCA_EXEC:?请设置 ORCA 驱动绝对路径}"']
    for job in jobs:
        lines.append(f'(cd {shlex.quote(job)} && "$ORCA_EXEC" calc.inp > calc.out 2>&1 && '
                     "grep -q 'ORCA TERMINATED NORMALLY' calc.out)")
    (root/name).write_text('\n'.join(lines)+'\n')


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    jobs = ['br-gas', 'br-smd', 'br-smd18', 'water-opt']
    for job in jobs:
        folder = root/job; folder.mkdir()
        shutil.copy2(HERE/f'{job}.inp', folder/'calc.inp')
        xyz = '1\nBromide; angstrom\nBr 0 0 0\n' if job.startswith('br-') else '3\nWater starting geometry; angstrom\nO 0 0 0\nH .77 0 .60\nH -.77 0 .60\n'
        (folder/'structure.xyz').write_text(xyz)
        if job == 'water-opt':
            shutil.copy2(HERE/'cm5.menu', folder/'cm5.menu')
    script(root, jobs, 'run-initial.sh')
    (root/'jobs.json').write_text(json.dumps({'initial': jobs}, indent=2)+'\n')
    return jobs


def prepare_solvents(root):
    source = root/'water-opt'
    text = (source/'calc.out').read_text()
    if 'ORCA TERMINATED NORMALLY' not in text or 'THE OPTIMIZATION HAS CONVERGED' not in text:
        raise ValueError('水的优化未正常结束并收敛')
    if any((root/name).exists() for name in ['water-smd', 'water-gil']):
        raise FileExistsError('溶剂任务已存在，不覆盖')
    jobs = ['water-smd', 'water-gil']
    for name in jobs:
        folder = root/name; folder.mkdir()
        shutil.copy2(HERE/f'{name}.inp', folder/'calc.inp')
        shutil.copy2(source/'calc.xyz', folder/'structure.xyz')
    script(root, jobs, 'run-solvents.sh')
    record = json.loads((root/'jobs.json').read_text()); record['solvents'] = jobs
    record['water_geometry_sha256'] = hashlib.sha256((source/'calc.xyz').read_bytes()).hexdigest()
    (root/'jobs.json').write_text(json.dumps(record, indent=2)+'\n')
    return jobs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, required=True)
    parser.add_argument('--stage', choices=['initial', 'solvents'], default='initial')
    args = parser.parse_args()
    print(prepare(args.work_root) if args.stage == 'initial' else prepare_solvents(args.work_root))
