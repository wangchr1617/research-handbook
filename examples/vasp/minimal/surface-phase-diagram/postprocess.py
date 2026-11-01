"""用法：python3 postprocess.py [--source 上游目录]；从实际输出检查参考态、约束与覆盖度能量。"""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from ase.io import read


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("."))
    a = p.parse_args()
    source = a.source.resolve()
    root = Path.cwd()
    # 跨案例复用前先核对全部科学输入，避免把其他构型当作同一参考数据。
    for pattern in ["POSCAR.*", "INCAR.*", "KPOINTS.*"]:
        for f in root.glob(pattern):
            if (
                not (source / f.name).is_file()
                or f.read_bytes() != (source / f.name).read_bytes()
            ):
                raise SystemExit(f"复用输入不一致：{f.name}")
    energies = {}
    geometry = {}
    for name in ["clean", "half", "full", "h2"]:
        work = source / name
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=work, check=True
        )
        out = (work / "OUTCAR").read_text(errors="replace")
        if name != "clean" and "reached required accuracy" not in out:
            raise SystemExit(f"{name} 优化未收敛")
        tree = ET.parse(work / "vasprun.xml").getroot()
        e = tree.findall("calculation")[-1].find("energy/i[@name='e_0_energy']")
        energies[name] = float(e.text)
        initial = read(work / "POSCAR")
        frames = read(work / "vasprun.xml", index=":")
        if name in ["half", "full"]:
            delta = np.array(
                [
                    f.get_scaled_positions(wrap=False)[:8]
                    - initial.get_scaled_positions(wrap=False)[:8]
                    for f in frames
                ]
            )
            delta -= np.rint(delta)
            delta = delta @ initial.cell.array
            # XML 坐标只保留有限小数位；末态另用高精度 CONTCAR 核对。
            final = read(work / "CONTCAR")
            final_delta = (
                final.get_scaled_positions(wrap=False)[:8]
                - initial.get_scaled_positions(wrap=False)[:8]
            )
            final_delta -= np.rint(final_delta)
            if (
                np.max(np.abs(delta)) > 1e-6
                or np.max(np.abs(final_delta @ initial.cell.array)) > 1e-8
            ):
                raise SystemExit("固定的金属基底发生移动")
            forces = frames[-1].get_forces(apply_constraint=False)[8:]
            if np.max(np.linalg.norm(forces, axis=1)) > 0.021:
                raise SystemExit("自由吸附原子受力尚未收敛")
            geometry[name] = {
                "hydrogens": len(initial) - 8,
                "max_adsorbate_force_eV_A": float(
                    np.max(np.linalg.norm(forces, axis=1))
                ),
            }
    cell = read(source / "clean/POSCAR").cell.array
    area = float(np.linalg.norm(np.cross(cell[0], cell[1])))
    ads = {
        name: energies[name] - energies["clean"] - number * 0.5 * energies["h2"]
        for name, number in [("half", 1), ("full", 2)]
    }
    if not np.isfinite(list(energies.values())).all():
        raise SystemExit("能量不是有限值")
    result = {
        "energies_E0_eV": energies,
        "adsorption_total_eV": ads,
        "area_A2": area,
        "adsorbates": geometry,
        "reference": "n_H/2 times relaxed H2; substrate atoms fixed; one active surface",
    }
    Path("adsorption-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    mu = np.linspace(-1.0, 0.0, 201)  # 相对于 1/2 E(H2) 的每 H 化学势，eV。
    omega = (
        np.column_stack([np.zeros_like(mu), ads["half"] - mu, ads["full"] - 2 * mu])
        / area
    )
    stable = np.argmin(omega, axis=1)
    crossings = {
        "clean_half_eV": ads["half"],
        "half_full_eV": ads["full"] - ads["half"],
        "clean_full_eV": ads["full"] / 2,
    }
    np.savetxt(
        "surface-grand-potentials.dat",
        np.column_stack([mu, omega, stable]),
        header="delta_muH_eV gamma_clean_eV_A2 gamma_half_eV_A2 gamma_full_eV_A2 stable_index",
    )
    Path("phase-results.json").write_text(
        json.dumps(
            {
                "area_A2": area,
                "delta_mu_H_range_eV": [-1.0, 0.0],
                "candidate_coverages_ML": [0, 0.5, 1],
                "stable_indices_in_range": np.unique(stable).tolist(),
                "formal_pair_crossings_eV": crossings,
                "normalization": "one active surface, no factor of 2",
            },
            indent=2,
        )
        + "\n"
    )
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
