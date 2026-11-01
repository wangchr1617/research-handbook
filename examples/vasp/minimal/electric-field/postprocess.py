"""用法：python3 postprocess.py；核对零永久偶极的 H2 在正负场下的对称性。"""

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

FIELD = 0.02  # VASP EFIELD 参数，eV/Å；方向与通常物理电场定义相反。


def main():
    root = Path.cwd()
    result = {}
    for name, field in [("minus", -FIELD), ("zero", 0), ("plus", FIELD)]:
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=name, check=True
        )
        xml = ET.parse(root / name / "vasprun.xml").getroot()
        value = xml.find(".//parameters//i[@name='EFIELD']")
        if value is None or abs(float(value.text) - field) > 1e-10:
            raise SystemExit("场强参数未实际生效")
        text = (root / name / "OUTCAR").read_text(errors="replace")
        rows = re.findall(
            r"dipolmoment\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", text
        )
        if not rows:
            raise SystemExit("未找到偶极矩输出")
        result[name] = {
            "energy_eV": json.loads((root / name / "results.json").read_text())[
                "free_energy_eV"
            ],
            "dipole_eA": list(map(float, rows[-1])),
            "EFIELD_eV_A": field,
        }
    minus, zero, plus = [result[s] for s in ["minus", "zero", "plus"]]
    dipoles = np.array([result[s]["dipole_eA"] for s in ["minus", "zero", "plus"]])
    curvature = (
        plus["energy_eV"] + minus["energy_eV"] - 2 * zero["energy_eV"]
    ) / FIELD**2
    if (
        not np.isfinite(dipoles).all()
        or abs(plus["energy_eV"] - minus["energy_eV"]) > 1e-5
        or abs(plus["dipole_eA"][2] + minus["dipole_eA"][2]) > 1e-4
        or abs(plus["dipole_eA"][2]) < 1e-4
        or curvature >= 0
    ):
        raise SystemExit("正负场对称性或诱导响应检查失败")
    result["energy_second_difference_eV_per_field_squared"] = curvature
    Path("field-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
