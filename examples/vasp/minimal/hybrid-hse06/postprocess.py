"""用法：python3 postprocess.py；核对 HSE06 设置及同一网格的采样带隙。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from read_eigen import read_eigen, sampled_gap


def main():
    result = {}
    points = []
    for stage in ["pbe", "hse06"]:
        subprocess.run(
            [sys.executable, str(Path.cwd() / "check_vasp.py")], cwd=stage, check=True
        )
        k, values, p = read_eigen(stage)
        points.append(k)
        if not np.isfinite(values).all():
            raise SystemExit("非有限本征值")
        if stage == "hse06" and (
            p.get("LHFCALC") != "T"
            or abs(float(p["HFSCREEN"]) - 0.2) > 1e-9
            or abs(float(p["AEXX"]) - 0.25) > 1e-9
        ):
            raise SystemExit("HSE06 设置未实际生效")
        result[stage] = {
            "sampled_gap_eV": sampled_gap(values),
            "irreducible_kpoints": len(k),
        }
    if not np.allclose(points[0], points[1]):
        raise SystemExit("两种泛函 k 点不同")
    if result["hse06"]["sampled_gap_eV"] - result["pbe"]["sampled_gap_eV"] < 0.01:
        raise SystemExit("未观察到硅的 HSE06 带隙变化")
    Path("hse-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
