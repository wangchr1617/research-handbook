"""用法：python3 postprocess.py；核对同构型、溶剂项及两种环境的总能差。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read


def main():
    root = Path.cwd()
    data = {}
    for name in ["vacuum", "solvent"]:
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=name, check=True
        )
        data[name] = json.loads((root / name / "results.json").read_text())[
            "free_energy_eV"
        ]
    if (root / "vacuum/POTCAR").read_bytes() != (root / "solvent/POTCAR").read_bytes():
        raise SystemExit("POTCAR 不一致")
    for f in ["POSCAR", "KPOINTS"]:
        if (root / "vacuum" / f).read_bytes() != (root / "solvent" / f).read_bytes():
            raise SystemExit(f"{f} 不一致")
    for name in ["vacuum", "solvent"]:
        if not np.allclose(
            read(root / name / "POSCAR").positions,
            read(root / name / "CONTCAR").positions,
            atol=1e-6,
        ):
            raise SystemExit("单点构型发生变化")
    terms = re.findall(
        r"Solvation\s+Ediel_sol\s*=\s*([-+0-9.Ee]+)",
        (root / "solvent/OUTCAR").read_text(errors="replace"),
    )
    if not terms or not np.isfinite(float(terms[-1])) or abs(float(terms[-1])) < 1e-8:
        raise SystemExit("未找到有效 VASPsol 溶剂能项，请核对程序版本")
    data["last_Ediel_sol_eV"] = float(terms[-1])
    data["solvent_minus_vacuum_eV"] = data["solvent"] - data["vacuum"]
    Path("solvation-results.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
