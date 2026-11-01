"""用法：python3 run.py；先按 POTCAR.spec 准备授权PAW数据，单核执行。"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ase.io import read, write

CASE = "berry-polarization"
exe = shutil.which(os.environ.get("VASP_EXEC", "vasp_std"))
if not exe or not Path("POTCAR").is_file():
    raise SystemExit("请准备 VASP_EXEC 和 POTCAR")
for stage in json.loads(Path("stages.json").read_text()):
    work = Path(stage)
    if work.exists():
        raise SystemExit(f"{stage} 已存在，请用干净目录")
    work.mkdir()
    for f in ["POSCAR", "POTCAR", "KPOINTS"]:
        shutil.copy(f, work / f)
    if CASE == "berry-polarization":
        atoms = read("POSCAR", format="vasp")
        # 位移单位Å，沿实验室z轴移动S原子，保持晶胞与其他坐标不变。
        atoms.positions[1, 2] += {"minus": -0.01, "zero": 0.0, "plus": 0.01}[stage]
        write(work / "POSCAR", atoms, format="vasp", direct=True, vasp5=True)
    shutil.copy("INCAR." + stage, work / "INCAR")
    with (work / "vasp.log").open("w") as out:
        subprocess.run(
            [exe], cwd=work, stdout=out, stderr=subprocess.STDOUT, check=True
        )
    subprocess.run(
        [sys.executable, str(Path("check_vasp.py").resolve())], cwd=work, check=True
    )
