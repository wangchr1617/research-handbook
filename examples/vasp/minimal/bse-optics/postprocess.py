"""用法：python3 postprocess.py；核对筛选截断及 BSE 实际介电谱。"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from read_results import completed, qp_table


def main():
    for stage in ["scf", "exact", "gw", "bse"]:
        completed(stage)
    qp_table()
    cutoff = []
    for stage in ["gw", "bse"]:
        text = Path(stage, "INCAR").read_text()
        cutoff.append(
            float(
                next(
                    l.split("=")[1]
                    for l in text.splitlines()
                    if l.startswith("ENCUTGW")
                )
            )
        )
    if cutoff[0] != cutoff[1]:
        raise SystemExit("GW 与 BSE 响应截断不一致")
    root = ET.parse("bse/vasprun.xml").getroot()
    data = np.array(
        [
            [float(v) for v in row.text.split()]
            for row in root.findall(".//dielectricfunction/imag/array/set/r")
        ]
    )
    transitions = np.array(
        [
            [float(v) for v in row.text.split()]
            for row in root.findall(".//varray[@name='opticaltransitions']/v")
        ]
    )
    if (
        data.ndim != 2
        or data.shape[1] != 7
        or not np.isfinite(data).all()
        or np.max(data[:, 1:4]) <= 0
        or transitions.size == 0
        or not np.isfinite(transitions).all()
        or np.min(transitions[:, 0]) <= 0
    ):
        raise SystemExit("BSE 介电谱或跃迁输出异常")
    np.savetxt("bse-dielectric.dat", data, header="E_eV eps2_xx yy zz xy yz zx")
    result = {
        "spectrum_points": len(data),
        "transitions": len(transitions),
        "ENCUTGW_eV": cutoff[0],
        "peak_energy_eV": float(data[np.argmax(data[:, 1:4].mean(axis=1)), 0]),
    }
    Path("bse-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
