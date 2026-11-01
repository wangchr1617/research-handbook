"""用法：python3 postprocess.py；检查固定 c、正交性与实际晶胞变化。"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from ase.io import read


def main():
    subprocess.run([sys.executable, "check_vasp.py"], check=True)
    out = Path("OUTCAR").read_text(errors="replace")
    if "reached required accuracy" not in out:
        raise SystemExit("晶胞优化未收敛")
    initial = read("POSCAR").cell.array
    cells = np.array(
        [
            [
                [float(v) for v in row.text.split()]
                for row in c.findall("structure/crystal/varray[@name='basis']/v")
            ]
            for c in ET.parse("vasprun.xml").getroot().findall("calculation")
        ]
    )
    final = read("CONTCAR").cell.array
    if np.max(np.abs(cells[:, 2] - initial[2])) > 1e-7:
        raise SystemExit("固定基矢 c 在优化过程中发生变化")
    if not np.allclose(final[2], initial[2], atol=1e-7):
        raise SystemExit("固定基矢 c 发生变化")
    if np.max(np.abs(cells - np.array([np.diag(np.diag(c)) for c in cells]))) > 1e-7:
        raise SystemExit("晶胞不再正交")
    if np.max(np.abs(final[:2] - initial[:2])) < 1e-3:
        raise SystemExit("面内晶胞未发生实际优化")
    data = {
        "initial_lengths_A": np.linalg.norm(initial, axis=1).tolist(),
        "final_lengths_A": np.linalg.norm(final, axis=1).tolist(),
        "steps": len(cells),
        "fixed_c_max_error_A": float(np.max(np.abs(cells[:, 2] - initial[2]))),
    }
    Path("cell-results.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
