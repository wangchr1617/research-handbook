"""用法：python3 postprocess.py；调用 easyunfold，检查完美硅的谱权重及原胞价带对应。"""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from easyunfold.unfold import UnfoldKSet
from run import restore_path_labels

WEIGHT_TOLERANCE = 1e-4  # 谱权重及价带权重和的数值容差。
ENERGY_TOLERANCE_EV = 0.01  # 原胞/超胞价带对照允许偏差，eV。


def main():
    root = Path.cwd()
    for stage in ["scf", "primitive-scf", "bands", "primitive-bands"]:
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=root / stage, check=True
        )
    executable = os.environ.get("EASYUNFOLD_EXEC", "easyunfold")
    with Path("unfold.log").open("w") as log:
        subprocess.run(
            [executable, "unfold", "calculate", "bands/WAVECAR"],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    data = UnfoldKSet.from_file("easyunfold.json")
    restore_path_labels(data)
    spectral = (
        data.get_spectral_weights()
    )  # 每个路径点下各对称等价点的能量与无量纲权重。
    tree = ET.parse("primitive-bands/vasprun.xml")
    sets = tree.findall("calculation")[-1].findall("eigenvalues/array/set/set/set")
    reference = np.array(
        [[float(row.text.split()[0]) for row in point.findall("r")] for point in sets]
    )
    if reference.shape != (len(spectral), 8):
        raise SystemExit("原胞对照的 k 点或能带数量不符")
    # 本例是完美、非自旋极化硅：原胞四条价带，2×1×1 超胞有八条价带。
    reference_vbm = float(reference[:, 3].max())
    supercell_vbm = float(max(point[0, :, :8, 0].max() for point in spectral))
    weight_errors, energy_errors = [], []
    for point, bands in zip(spectral, reference):
        if (
            not np.isfinite(point).all()
            or point[..., 1].min() < -WEIGHT_TOLERANCE
            or point[..., 1].max() > 1 + WEIGHT_TOLERANCE
        ):
            raise SystemExit("谱权重超出范围或包含非有限值")
        weight_errors.append(float(np.abs(point[0, :, :8, 1].sum(axis=-1) - 4).max()))
        for equivalent in point[0]:
            for energy, weight in equivalent[:8]:
                if weight > 1e-3:
                    energy_errors.append(
                        float(
                            np.min(
                                np.abs(
                                    (energy - supercell_vbm)
                                    - (bands[:4] - reference_vbm)
                                )
                            )
                        )
                    )
    maximum_weight_error = max(weight_errors)
    maximum_energy_error = max(energy_errors)
    if (
        maximum_weight_error > WEIGHT_TOLERANCE
        or maximum_energy_error > ENERGY_TOLERANCE_EV
    ):
        raise SystemExit("完美硅的价带谱权重和或原胞能量对应检查未通过")
    result = {
        "primitive_kpoints": len(spectral),
        "supercell_kpoints": int(Path("bands/KPOINTS").read_text().splitlines()[1]),
        "supercell_vbm_eV": supercell_vbm,
        "primitive_vbm_eV": reference_vbm,
        "maximum_valence_weight_sum_error": maximum_weight_error,
        "maximum_valence_energy_difference_eV": maximum_energy_error,
        "symmetry_averaging": True,
    }
    Path("unfolding-results.json").write_text(json.dumps(result, indent=2) + "\n")
    subprocess.run([sys.executable, str(root / "plot.py")], check=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
