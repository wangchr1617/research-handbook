"""核对晶胞传递、两种扩胞表示和显式 NEB 路径；不从语法通过推断科学收敛。

用法：python analyze.py --work-root WORK --output interfaces.json
坐标/晶胞单位 Å，CP2K 单点能量单位 Hartree。
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np


def read_input(file):
    text = Path(file).read_text()
    cell_block = re.search(r"&CELL\s*\n([\s\S]*?)&END CELL", text)[1]
    cell = np.array([[float(x) for x in re.search(rf"^\s*{key}\s+([^#\n]+)", cell_block, re.M)[1].split()] for key in "ABC"])
    coord_block = re.search(r"&COORD\s*\n([\s\S]*?)&END COORD", text)[1]
    rows = [line.split() for line in coord_block.splitlines() if line.strip()]
    xyz = np.array([[float(x) for x in row[1:]] for row in rows])
    geometry_pbc = re.search(r"PERIODIC\s+(\S+)", cell_block)[1]
    poisson = re.search(r"&POISSON\s*\n([\s\S]*?)&END POISSON", text)[1]
    repetitions = re.findall(r"MULTIPLE_UNIT_CELL\s+(\d+)\s+(\d+)\s+(\d+)", text)
    if repetitions:
        assert len(repetitions) == 2 and repetitions[0] == repetitions[1]
    rep = np.array([int(x) for x in repetitions[0]]) if repetitions else np.ones(3, dtype=int)
    return dict(cell_angstrom=cell.tolist(), coordinates_angstrom=xyz.tolist(),
                geometry_periodic=geometry_pbc, poisson_periodic=re.search(r"PERIODIC\s+(\S+)", poisson)[1],
                poisson_solver=re.search(r"PSOLVER\s+(\S+)", poisson)[1], repetitions=rep.tolist(),
                coordinate_atom_count=len(xyz), effective_atom_count=int(len(xyz) * np.prod(rep)),
                effective_volume_angstrom3=float(abs(np.linalg.det(cell)) * np.prod(rep)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.work_root
    result = {name: read_input(root / name / "cp2k.inp") for name in ["plain", "lattice", "tv", "replicated", "explicit", "vib", "isolated", "slab"]}
    expected = np.array([[8., 0, 0], [1., 7.5, 0], [.5, .3, 9.]])
    for name in ["lattice", "tv"]:
        assert np.array_equal(result[name]["cell_angstrom"], expected)
    assert result["lattice"] == result["tv"]
    assert result["plain"]["geometry_periodic"] == "XYZ"
    assert result["isolated"]["geometry_periodic"] == result["isolated"]["poisson_periodic"] == "NONE"
    assert result["isolated"]["poisson_solver"] == "WAVELET"
    assert result["slab"]["geometry_periodic"] == result["slab"]["poisson_periodic"] == "XY"
    base = np.array(result["lattice"]["coordinates_angstrom"])
    assert np.array_equal(result["explicit"]["coordinates_angstrom"], np.concatenate([base, base + expected[0]]))
    assert result["replicated"]["effective_atom_count"] == result["explicit"]["effective_atom_count"] == 6
    assert abs(result["replicated"]["effective_volume_angstrom3"] - result["explicit"]["effective_volume_angstrom3"]) < 1e-10
    energies = {}
    for name in ["replicated", "explicit"]:
        text = (root / name / "scf.out").read_text()
        assert "SCF run converged" in text and "PROGRAM ENDED AT" in text
        assert int(re.search(r"- Atoms:\s+(\d+)", text)[1]) == 6
        energy = float(re.search(r"ENERGY\| Total FORCE_EVAL.*?\[hartree\]\s+(-?\d+\.\d+)", text)[1])
        energies[name] = energy
    delta = abs(energies["replicated"] - energies["explicit"])
    assert delta < 1e-10
    result = dict(multiwfn="2026.7.15", cp2k="2026.2", input_models=result,
                  supercell_energy_hartree=energies, energy_difference_hartree=delta,
                  meaning="Input-format and representation comparison on an artificial periodic water array; not convergence or material-property benchmark")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(supercell_energy_difference_hartree=delta, effective_atoms=6)))


if __name__ == "__main__":
    main()
