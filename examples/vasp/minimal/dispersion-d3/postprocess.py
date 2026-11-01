"""用法：python3 postprocess.py；核对 D3(BJ) 修正能与同构型总能差。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np


def main():
    root = Path.cwd()
    result = {}
    for stage in ["pbe", "d3"]:
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=stage, check=True
        )
        result[stage] = json.loads((root / stage / "results.json").read_text())[
            "free_energy_eV"
        ]
    values = re.findall(
        r"Edisp\s*(?:\(eV\))?\s*=?\s*([-+0-9.Ee]+)",
        (root / "d3/OUTCAR").read_text(errors="replace"),
    )
    if not values:
        raise SystemExit("未找到实际 Edisp 色散项")
    correction = float(values[-1])
    difference = result["d3"] - result["pbe"]
    if (
        not np.isfinite(correction)
        or correction >= -1e-6
        or abs(difference - correction) > 1e-4
    ):
        raise SystemExit("色散修正或总能差不一致")
    result.update(
        dispersion_energy_eV=correction, total_energy_difference_eV=difference
    )
    Path("dispersion-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
