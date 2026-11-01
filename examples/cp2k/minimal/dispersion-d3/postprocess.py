"""用法：python3 postprocess.py；核对实际 D3(BJ) 色散能与两组总能差。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.units import Hartree


def main():
    root = Path.cwd()
    result = {}
    for name in ["pbe", "d3"]:
        subprocess.run(
            [sys.executable, str(root / "check_cp2k.py")], cwd=name, check=True
        )
        result[name] = json.loads((root / name / "results.json").read_text())
    text = (root / "d3/cp2k.out").read_text(errors="replace")
    values = re.findall(r"(?im)^\s*Dispersion energy:\s*([-+0-9.Ee]+)\s*$", text)
    if not values:
        raise SystemExit("未找到实际色散能项")
    correction = float(values[-1]) * Hartree
    difference = result["d3"]["energy_eV"] - result["pbe"]["energy_eV"]
    if (
        not np.isfinite(correction)
        or correction >= -1e-6
        or abs(correction - difference) > 1e-4
    ):
        raise SystemExit("色散修正或能量差不一致")
    result.update(
        dispersion_energy_eV=correction, total_energy_difference_eV=difference
    )
    Path("dispersion-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
