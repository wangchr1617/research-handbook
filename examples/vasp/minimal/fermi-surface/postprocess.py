"""用法：python3 postprocess.py；核对完整网格、电子数及跨越费米能的能带。"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from ase.io import read
from read_eigen import read_eigen


def main():
    root = Path.cwd()
    for stage in ["scf", "grid"]:
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=stage, check=True
        )
    n = json.loads(Path("grid.json").read_text())["grid"]
    k, values, _ = read_eigen("grid")
    expected = (
        np.array(np.meshgrid(*([np.arange(n) / n - 0.5] * 3), indexing="ij"))
        .reshape(3, -1)
        .T
    )
    if (
        values.shape[0] != 1
        or len(k) != n**3
        or not np.allclose(k, expected, atol=1e-9)
    ):
        raise SystemExit("不是预期的完整非自旋网格")
    fermi = float(
        ET.parse("grid/vasprun.xml")
        .getroot()
        .findall("calculation")[-1]
        .find('dos/i[@name="efermi"]')
        .text
    )
    e = values[0, :, :, 0]
    occupation = values[0, :, :, 1]
    electrons = float(2 * np.mean(occupation.sum(axis=1)))
    crossing = np.flatnonzero((e.min(axis=0) < fermi) & (e.max(axis=0) > fermi))
    if not np.isfinite(e).all() or not len(crossing) or abs(electrons - 3) > 0.25:
        raise SystemExit("费米面穿越、电子数或本征值异常")
    bands = e.reshape(n, n, n, -1)
    reciprocal = read("POSCAR").cell.reciprocal().array * 2 * np.pi
    np.savez_compressed(
        "fermi-grid.npz", energies=bands, fermi=fermi, reciprocal=reciprocal
    )
    result = {
        "grid": n,
        "kpoints": len(k),
        "fermi_eV": fermi,
        "crossing_bands_1based": (crossing + 1).tolist(),
        "grid_electrons": electrons,
    }
    Path("fermi-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
