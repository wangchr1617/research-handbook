"""用法：python3 postprocess.py；用 VASPKIT 提取 NiO 自旋 DOS，核对 U 与 J。"""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np


def main():
    result = {}
    root = Path.cwd()
    for stage, u in [("u0", 0), ("u4", 4)]:
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=stage, check=True
        )
        tree = ET.parse(root / stage / "vasprun.xml").getroot()
        p = {
            node.attrib["name"]: (node.text or "").strip()
            for node in tree.findall(".//parameters//v")
            + tree.findall(".//parameters//i")
        }
        if (
            p.get("LDAU") != "T"
            or int(p["LDAUTYPE"]) != 2
            or abs(float(p["LDAUU"].split()[0]) - u) > 1e-8
            or not np.allclose(list(map(float, p["LDAUJ"].split())), 0)
            or p["LDAUL"].split()[0] != "2"
        ):
            raise SystemExit("DFT+U 参数未实际生效")
        with (root / stage / "vaspkit.log").open("w") as log:
            subprocess.run(
                [os.environ.get("VASPKIT_EXEC", "vaspkit")],
                cwd=stage,
                input="111\n",
                text=True,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )
        data = np.loadtxt(root / stage / "TDOS.dat", ndmin=2)
        if (
            data.shape[1] < 3
            or not np.isfinite(data).all()
            or np.max(np.abs(data[:, 1:3])) < 1e-6
        ):
            raise SystemExit("DOS 输出异常")
        result[stage] = {"U_eff_eV": u, "dos_rows": len(data)}
    Path("hubbard-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
