"""用法：python3 postprocess.py；收集体积和总能，生成 EOS.in 并调用 VASPKIT 205。"""

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from ase.io import read


def main():
    points = []
    for folder in sorted(Path(".").glob("volume-*")):
        atoms = read(folder / "POSCAR", format="vasp")
        root = ET.parse(folder / "vasprun.xml").getroot()
        energy = float(
            root.findall("calculation")[-1].find("energy/i[@name='e_0_energy']").text
        )
        points.append((atoms.get_volume(), energy))
    data = np.asarray(points)
    if len(points) < 5 or not np.isfinite(data).all():
        raise SystemExit("状态方程拟合需要至少五组有效体积与能量")
    if np.argmin(data[:, 1]) in [0, len(data) - 1]:
        raise SystemExit("能量极小值不在扫描范围内，请扩大体积范围")
    np.savetxt("energy-volume.dat", data, header="Volume(A^3) Energy(eV)")
    # VASPKIT EOS.in：体系名、原子数、方程类型、拟合区间、数据点数和体积能量。
    lines = [
        "Si",
        "2",
        "2",
        f"{data[:, 0].min():.10f} {data[:, 0].max():.10f} 101",
        str(len(data)),
    ]
    lines += [f"{volume:.12f} {energy:.12f}" for volume, energy in points]
    Path("EOS.in").write_text("\n".join(lines) + "\n")
    executable = os.environ.get("VASPKIT_EXEC", "vaspkit")
    with Path("vaspkit.in").open() as commands, Path("vaspkit.log").open("w") as log:
        subprocess.run(
            [executable],
            stdin=commands,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    text = Path("vaspkit.log").read_text(errors="replace")
    if re.search(r"forrtl:|Error:", text):
        raise SystemExit("VASPKIT 拟合失败，请检查 vaspkit.log")
    result = {}
    for label, key in [
        ("V0", "volume_A3_cell"),
        ("E0", "energy_eV_cell"),
        ("B0", "bulk_modulus_GPa"),
    ]:
        match = re.search(r"^\s*" + label + r"\s*=\s*([-+0-9.Ee]+)", text, re.MULTILINE)
        if not match:
            raise SystemExit(f"缺少拟合参数 {label}")
        result[key] = float(match.group(1))
    if not (
        data[:, 0].min() < result["volume_A3_cell"] < data[:, 0].max()
        and result["bulk_modulus_GPa"] > 0
    ):
        raise SystemExit("拟合参数不合理，请检查扫描范围与数据")
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
