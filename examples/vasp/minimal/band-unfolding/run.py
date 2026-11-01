"""用法：python3 run.py [--ranks 2]；完美硅超胞反折叠，并计算原胞能带作对照。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from easyunfold.unfold import UnfoldKSet

SUPERCELL_MATRIX = "2 1 1"  # 超胞晶格 = M × 原胞晶格，此处 M 为对角矩阵。


def restore_path_labels(data):
    """按输入顶点核对标签，避免路径插值后标签错位。"""
    labels = {}
    for line in Path("KPOINTS.primitive").read_text().splitlines()[4:]:
        if "!" not in line:
            continue
        coordinates, label = line.split("!", 1)
        point = np.array(list(map(float, coordinates.split())))
        label = label.strip()
        if label.upper() == "GAMMA":
            label = "Γ"
        for index in np.flatnonzero(
            np.all(np.isclose(data.kpts_pc, point, atol=1e-9), axis=1)
        ):
            labels[int(index)] = label
    data.kpoint_labels = sorted(labels.items())
    Path("easyunfold.json").write_text(data.to_json())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    if args.ranks < 1:
        parser.error("MPI 进程数须为正整数")
    root = Path.cwd()
    if not (root / "POTCAR").is_file():
        raise SystemExit("请准备授权 Si POTCAR")
    easyunfold = os.environ.get("EASYUNFOLD_EXEC", "easyunfold")
    with Path("generate.log").open("w") as log:
        subprocess.run(
            [
                easyunfold,
                "generate",
                "POSCAR.primitive",
                "POSCAR",
                "KPOINTS.primitive",
                "--matrix",
                SUPERCELL_MATRIX,
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    data = UnfoldKSet.from_file("easyunfold.json")
    restore_path_labels(data)
    # 原胞对照使用与反折叠完全相同的路径点，避免重复端点或插值规则差异。
    Path("KPOINTS.reference").write_text(
        "Primitive reference at exact unfolded points\n"
        + str(len(data.kpts_pc))
        + "\nReciprocal\n"
        + "".join(
            " ".join(f"{value:.10f}" for value in point) + " 1\n"
            for point in data.kpts_pc
        )
    )
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    stages = [
        ("scf", "POSCAR", "KPOINTS.scf", None),
        ("primitive-scf", "POSCAR.primitive", "KPOINTS.scf-primitive", None),
        ("bands", "POSCAR", "KPOINTS_easyunfold", "scf"),
        ("primitive-bands", "POSCAR.primitive", "KPOINTS.reference", "primitive-scf"),
    ]
    for name, structure, kpoints, charge in stages:
        work = root / name
        if work.exists():
            raise SystemExit(f"{name} 已存在，请使用新目录或只做后处理")
        work.mkdir()
        for source, target in [
            (structure, "POSCAR"),
            (kpoints, "KPOINTS"),
            ("POTCAR", "POTCAR"),
        ]:
            shutil.copy2(root / source, work / target)
        incar = (root / ("INCAR.band" if charge else "INCAR.scf")).read_text()
        if name == "primitive-bands":
            incar = incar.replace("NBANDS = 16", "NBANDS = 8").replace(
                "LWAVE = .TRUE.", "LWAVE = .FALSE."
            )
        (work / "INCAR").write_text(incar)
        if charge:
            shutil.copy2(root / charge / "CHGCAR", work / "CHGCAR")
        with (work / "vasp.log").open("w") as log:
            subprocess.run(
                command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
            )
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=work, check=True
        )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
