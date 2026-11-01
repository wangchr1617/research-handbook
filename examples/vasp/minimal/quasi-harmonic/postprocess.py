"""用法：python3 postprocess.py；用 Phonopy 拟合五个体积的准谐自由能并绘图。"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import phonopy
from ase.units import GPa
from phonopy.interface.vasp import parse_set_of_forces

MESH = (8, 8, 8)  # 声子热力学积分的 q 网格；不是 VASP 电子 k 网格。
TEMPERATURES_K = np.arange(0, 701, 100)  # 多提供一个温度点供数值微分使用。


def main():
    root = Path.cwd()
    directories = sorted(root.glob("volume-*/phonopy_disp.yaml"))
    if len(directories) < 5:
        raise SystemExit("QHA 至少需要五个体积")
    phonons, energies, minima = [], [], []
    for filename in directories:
        work = filename.parent
        phonon = phonopy.load(filename, produce_fc=False)
        outputs = sorted(work.glob("disp-*/vasprun.xml"))
        if len(outputs) != len(phonon.supercells_with_displacements):
            raise SystemExit(f"{work.name} 的位移输出不完整")
        for output in [work / "static/vasprun.xml", *outputs]:
            subprocess.run(
                [sys.executable, str(root / "check_vasp.py")],
                cwd=output.parent,
                check=True,
            )
        parsed = parse_set_of_forces(len(phonon.supercell), outputs, verbose=False)
        if not parsed:
            raise SystemExit(f"{work.name} 的 VASP 受力解析失败")
        phonon.forces = parsed["forces"]
        phonon.produce_force_constants()
        phonon.symmetrize_force_constants()
        phonon.run_mesh(MESH)
        minimum = float(phonon.mesh.frequencies.min())
        if minimum < -0.001:
            raise SystemExit(
                f"{work.name} 出现虚频 {minimum:g} THz，不能直接用于本例 QHA"
            )
        minima.append(minimum)
        tree = ET.parse(work / "static/vasprun.xml")
        energy = float(
            tree.findall("calculation")[-1].find("energy/i[@name='e_0_energy']").text
        )
        # 电子能量与体积均按 Phonopy 的两原子原胞归一化，不能混用 16 原子能量。
        ratio = len(phonon.supercell) / len(phonon.primitive)
        energies.append(energy / ratio)
        phonon.save(filename=str(work / "phonopy_params.yaml"))
        phonons.append(phonon)
    result = phonopy.run_qha(
        phonons,
        temperatures=TEMPERATURES_K,
        internal_energies=energies,
        mesh=MESH,
        eos="birch_murnaghan",
        verbose=True,
    )
    volumes = np.asarray(result.volumes)
    equilibrium = np.asarray(result.equilibrium_volumes)
    expansion = np.asarray(result.thermal_expansion)
    bulk = np.asarray(result.bulk_moduli) / GPa
    if (
        not all(np.isfinite(values).all() for values in [equilibrium, expansion, bulk])
        or (bulk <= 0).any()
    ):
        raise SystemExit("QHA 拟合出现非有限值或负体积模量")
    if (equilibrium <= volumes.min()).any() or (equilibrium >= volumes.max()).any():
        raise SystemExit("平衡体积超出采样范围，请扩展体积点，不应直接外推")
    output = {
        "phonopy_version": phonopy.__version__,
        "natom_primitive": len(phonons[0].primitive),
        "volumes_A3": volumes.tolist(),
        "static_energies_eV": energies,
        "minimum_mesh_frequencies_THz": minima,
        "temperatures_K": result.temperatures.tolist(),
        "equilibrium_volumes_A3": equilibrium.tolist(),
        "volumetric_expansion_K_inv": expansion.tolist(),
        "bulk_moduli_GPa": bulk.tolist(),
    }
    Path("qha-results.json").write_text(json.dumps(output, indent=2) + "\n")
    np.savetxt(
        "e-v.dat",
        np.column_stack([volumes, energies]),
        header="Primitive-cell volume (A^3), static energy (eV)",
    )
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
