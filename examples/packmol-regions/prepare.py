"""生成周期水盒与定向水层的几何装填输入；python prepare.py --work-root NEW。"""
import argparse
import json
import math
from pathlib import Path


def prepare(root):
    root.mkdir(parents=True, exist_ok=False)
    bond=.96; theta=math.radians(104.5/2)
    x=bond*math.sin(theta);z=bond*math.cos(theta)
    water=f'3\nRigid water geometry; angstrom\nO 0 0 0\nH {x:.10f} 0 {z:.10f}\nH {-x:.10f} 0 {z:.10f}\n'
    specs={
        'periodic': {'water_count':32,'seed':314159,'box_Angstrom':[12.,12.,12.]},
        'oriented-layer': {'water_count':16,'seed':161803,'box_Angstrom':None}}
    common='tolerance 2.0\nprecision 1e-8\nfiletype xyz\noutput unused.xyz\n'
    periodic=common+'''seed 314159
pbc 12.0 12.0 12.0
structure water.xyz
  number 32
end structure
'''
    layer=common+'''seed 161803
structure water.xyz
  number 16
  inside box 0.0 0.0 0.0 12.0 12.0 4.0
  atoms 1
    inside box 0.0 0.0 2.0 12.0 12.0 2.2
  end atoms
  atoms 2 3
    over plane 0.0 0.0 1.0 2.5
  end atoms
end structure
'''
    for name,content in [('periodic',periodic),('oriented-layer',layer)]:
        p=root/name;p.mkdir();(p/'water.xyz').write_text(water);(p/'packmol.inp').write_text(content)
    (root/'cases.json').write_text(json.dumps(specs,indent=2)+'\n')
    (root/'run.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
: "${PACKMOL_EXEC:?请设置 Packmol 绝对路径}"
for stage in periodic oriented-layer; do
  (cd "$stage" && "$PACKMOL_EXEC" -i packmol.inp -o packed.xyz > packmol.out 2>&1 && grep -q 'Success!' packmol.out)
done
''')
    return specs


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work-root',type=Path,required=True)
    args=parser.parse_args();prepare(args.work_root)
