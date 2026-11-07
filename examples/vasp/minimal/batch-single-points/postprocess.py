"""用法：python3 postprocess.py；复用仓库导出器，核对能量、受力与位力单位/符号。"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from ase.io import read
from ase.units import GPa
from run import CASES


def main():
    root = Path.cwd()
    converter = os.environ.get("VASP2XYZ_SCRIPT")  # 可指定完整仓库之外的导出脚本路径。
    if not converter:
        converter = next(
            (
                parent / "scripts/structure/vasp_to_xyz.py"
                for parent in Path(__file__).resolve().parents
                if (parent / "scripts/structure/vasp_to_xyz.py").is_file()
            ),
            None,
        )
    if not converter:
        raise SystemExit("请使用完整仓库，或设置 VASP2XYZ_SCRIPT")
    for name in CASES:
        subprocess.run(
            [sys.executable, str(Path(__file__).with_name("check_vasp.py"))],
            cwd=root / "runs" / name,
            check=True,
        )
    records = []
    # 先在临时目录核验，成功后才替换本案例生成的数据文件。
    with tempfile.TemporaryDirectory(prefix=".labels-", dir=root) as temporary:
        output = Path(temporary) / "labels.xyz"
        subprocess.run(
            [
                sys.executable,
                str(converter),
                "runs",
                "-o",
                str(output),
                "--frames",
                "last",
                "--converged",
                "--energy",
                "free",
            ],
            check=True,
        )
        frames = read(output, index=":", format="extxyz")
        if len(frames) != len(CASES):
            raise SystemExit("导出帧数与计算数不一致")
        for atoms in frames:
            name = atoms.info["config_type"]
            tree = ET.parse(root / "runs" / name / "vasprun.xml")
            last = tree.findall("calculation")[-1]
            energy = float(last.find("energy/i[@name='e_fr_energy']").text)
            forces = np.array(
                [
                    list(map(float, row.text.split()))
                    for row in last.findall("varray[@name='forces']/v")
                ]
            )
            stress_kbar = np.array(
                [
                    list(map(float, row.text.split()))
                    for row in last.findall("varray[@name='stress']/v")
                ]
            )
            raw_cell = np.array(
                [
                    list(map(float, row.text.split()))
                    for row in last.findall("structure/crystal/varray[@name='basis']/v")
                ]
            )
            raw_fractional = np.array(
                [
                    list(map(float, row.text.split()))
                    for row in last.findall("structure/varray[@name='positions']/v")
                ]
            )
            difference = (atoms.get_scaled_positions() - raw_fractional + 0.5) % 1 - 0.5
            if (
                not np.allclose(atoms.cell, raw_cell, atol=1e-8)
                or np.linalg.norm(difference @ raw_cell) > 1e-7
            ):
                raise SystemExit(f"{name} 的晶胞或坐标回读不一致")
            # VASP 压缩应力为正，NEP 位力 = -ASE 应力×体积，因此这里取正号。
            virial = stress_kbar * 0.1 * GPa * atoms.get_volume()
            if (
                not atoms.pbc.all()
                or not np.isclose(atoms.get_potential_energy(), energy, atol=1e-7)
                or not np.allclose(atoms.get_forces(), forces, atol=1e-7)
                or not np.allclose(atoms.info["virial"], virial, atol=1e-6)
            ):
                raise SystemExit(f"{name} 的能量、力、位力或周期性回读不一致")
            records.append(
                {
                    "case": name,
                    "energy_eV": energy,
                    "max_force_eV_A": float(np.linalg.norm(forces, axis=1).max()),
                    "virial_eV": virial.tolist(),
                }
            )
        shutil.copy2(output, "labeled-structures.xyz")
    Path("batch-results.json").write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
