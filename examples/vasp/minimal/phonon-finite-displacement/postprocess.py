"""运行：python3 postprocess.py；从本目录 VASP 输出提取能量、受力与收敛信息。"""

import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    root = ET.parse("vasprun.xml").getroot()
    steps = root.findall("calculation")
    if not steps:
        raise SystemExit("vasprun.xml 中没有计算步骤")
    last = steps[-1]
    energy = {i.attrib["name"]: float(i.text) for i in last.findall("energy/i")}
    forces = [
        [float(v) for v in row.text.split()]
        for row in last.findall("varray[@name='forces']/v")
    ]
    out = Path("OUTCAR").read_text(errors="replace")
    result = {
        "energy_eV": energy.get("e_0_energy"),
        "free_energy_eV": energy.get("e_fr_energy"),
        "ionic_steps": len(steps),
        "max_force_eV_A": max(
            (math.sqrt(sum(v * v for v in row)) for row in forces), default=None
        ),
        "electronic_converged": "EDIFF is reached" in out
        and all(len(c.findall("scstep")) < 100 for c in steps),
        "max_scf_steps": max(len(c.findall("scstep")) for c in steps),
        "ionic_converged": "reached required accuracy" in out,
        "completed": "General timing and accounting" in out,
    }
    modes = re.findall(r"f(\s*|/i)\s*=\s*([-+0-9.Ee]+)\s+THz", out)
    frequencies = [(-1 if kind == "/i" else 1) * float(value) for kind, value in modes]
    result["frequencies_THz"] = frequencies
    if len(frequencies) != 6 or min(frequencies) < -0.001:
        raise SystemExit("硅原胞的 Γ 点振动模式异常，请检查 OUTCAR")
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["completed"] or not result["electronic_converged"]:
        raise SystemExit("计算未正常结束或电子迭代未收敛")


if __name__ == "__main__":
    main()
