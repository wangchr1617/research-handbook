"""用法：python3 postprocess.py；用 phono3py 建立二/三阶力常数，计算 RTA 晶格热导率。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import phono3py
from phonopy.interface.vasp import parse_set_of_forces

Q_MESH = (5, 5, 5)  # 三声子散射积分的 q 网格，研究计算需加密。
TEMPERATURES_K = (100, 200, 300, 400, 500, 600)
SMEARING_THZ = 0.2  # 能量守恒条件的高斯展宽，单位 THz。


def main():
    root = Path.cwd()
    phonon = phono3py.load("phono3py_disp.yaml", produce_fc=False)
    cells = phonon.supercells_with_displacements
    included = [index for index, cell in enumerate(cells) if cell is not None]
    files = [root / f"disp-{index + 1:05d}/vasprun.xml" for index in included]
    for filename in files:
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")],
            cwd=filename.parent,
            check=True,
        )
    parsed = parse_set_of_forces(len(phonon.supercell), files, verbose=False)
    if not parsed:
        raise SystemExit("VASP 受力解析失败")
    forces = np.zeros((len(cells), len(phonon.supercell), 3))
    maximum_drift = 0.0
    for index, force in zip(included, parsed["forces"]):
        force = np.asarray(force)
        if not np.isfinite(force).all():
            raise SystemExit("受力含非有限值")
        maximum_drift = max(maximum_drift, float(np.linalg.norm(force.sum(axis=0))))
        # 消除有限数值精度导致的整体受力漂移，不代替电子收敛检查。
        forces[index] = force - force.mean(axis=0)
    phonon.forces = forces
    harmonic = []
    for target in phonon.phonon_supercells_with_displacements:
        matches = [
            i
            for i in included
            if np.allclose(cells[i].cell, target.cell)
            and np.allclose(cells[i].scaled_positions, target.scaled_positions)
        ]
        if not matches:
            raise SystemExit("本例二阶位移不能从三阶任务复用，请另算二阶受力")
        harmonic.append(forces[matches[0]])
    phonon.phonon_forces = harmonic
    phonon.produce_fc2(fc_calculator="traditional")
    phonon.symmetrize_fc2(use_symfc_projector=False)
    phonon.produce_fc3(fc_calculator="traditional")
    phonon.symmetrize_fc3(use_symfc_projector=False)
    if not np.isfinite(phonon.fc2).all() or not np.isfinite(phonon.fc3).all():
        raise SystemExit("力常数含非有限值")
    phonon.save(filename="phono3py_params.yaml", settings={"force_constants": True})
    phonon.mesh_numbers = Q_MESH
    phonon.sigmas = [SMEARING_THZ]
    phonon.init_phph_interaction(exclude_gamma_acoustic=True)
    phonon.run_phonon_solver()
    frequencies, _, _ = phonon.get_phonon_data()
    minimum = float(frequencies.min())
    if minimum < -0.001:
        raise SystemExit(f"出现明显虚频 {minimum:g} THz，请先处理结构与数值精度")
    phonon.run_thermal_conductivity(
        temperatures=TEMPERATURES_K, is_LBTE=False, write_kappa=True
    )
    conductivity = np.asarray(phonon.thermal_conductivity.kappa)[0]
    if (
        conductivity.shape != (len(TEMPERATURES_K), 6)
        or not np.isfinite(conductivity).all()
        or (conductivity[:, :3] <= 0).any()
    ):
        raise SystemExit("热导率结果不完整、非有限或纵向分量非正")
    if not np.allclose(conductivity[:, :3], conductivity[:, :1], rtol=1e-3, atol=1e-4):
        raise SystemExit("立方硅的纵向热导率不符合对称性")
    output = {
        "phono3py_version": phono3py.__version__,
        "force_calculations": len(included),
        "q_mesh": list(Q_MESH),
        "smearing_THz": SMEARING_THZ,
        "temperatures_K": list(TEMPERATURES_K),
        "kappa_W_mK": conductivity.tolist(),
        "voigt_order": ["xx", "yy", "zz", "yz", "xz", "xy"],
        "minimum_frequency_THz": minimum,
        "maximum_force_drift_eV_A": maximum_drift,
        "method": "RTA; three-phonon scattering only",
    }
    Path("thermal-conductivity-results.json").write_text(
        json.dumps(output, indent=2) + "\n"
    )
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
