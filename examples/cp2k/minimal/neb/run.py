"""用法：python3 run.py [--ranks 5] [--stage endpoints|neb|all]；优化端点并运行 CP2K CI-NEB。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.geometry import find_mic
from ase.io import read, write


def launch(executable, folder, input_name, output_name, ranks=1):
    output = folder / output_name
    if output.exists():
        raise SystemExit(f"{output} 已存在；请先移走旧输出，避免追加混入本次结果")
    command = [executable] if ranks == 1 else ["mpirun", "-np", str(ranks), executable]
    with (folder / "launch.log").open("w") as log:
        subprocess.run(
            [*command, "-i", input_name, "-o", output_name],
            cwd=folder,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    text = output.read_text(errors="replace")
    if "PROGRAM ENDED AT" not in text or "SCF run NOT converged" in text:
        raise SystemExit(f"请检查 {output} 的结束与 SCF 状态")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=5)
    parser.add_argument("--stage", choices=["endpoints", "neb", "all"], default="all")
    args = parser.parse_args()
    if args.ranks <= 0:
        raise SystemExit("MPI 进程数须为正整数")
    root = Path.cwd()
    executable = os.environ.get("CP2K_EXEC", "cp2k.psmp")
    if args.stage in ["endpoints", "all"]:
        for name in ["initial", "final"]:
            work = root / name
            work.mkdir(exist_ok=True)
            shutil.copy2(root / f"{name}.xyz", work / "structure.xyz")
            shutil.copy2(root / "endpoint.inp", work / "cp2k.inp")
            launch(executable, work, "cp2k.inp", "cp2k.out")
            if "GEOMETRY OPTIMIZATION COMPLETED" not in (work / "cp2k.out").read_text():
                raise SystemExit(f"{name} 端点未收敛")
    if args.stage == "endpoints":
        return
    endpoints = []
    for name in ["initial", "final"]:
        work = root / name
        if "GEOMETRY OPTIMIZATION COMPLETED" not in (work / "cp2k.out").read_text():
            raise SystemExit(f"{name} 端点未收敛，不能开始 NEB")
        files = list(work.glob("endpoint-FINAL-*.xyz"))
        if len(files) != 1:
            raise SystemExit(f"请在 {work} 保留本次优化的唯一 FINAL XYZ")
        endpoints.append(read(files[0]))
    initial, final = endpoints
    if not np.allclose(initial.cell, final.cell):
        raise SystemExit("两个端点晶胞不一致")
    # 统一周期映像，再让 CP2K 原生插值，避免跨越较长的晶胞路径。
    displacement, _ = find_mic(
        final.positions - initial.positions, cell=initial.cell, pbc=initial.pbc
    )
    final.positions = initial.positions + displacement
    write(root / "replica-00.xyz", initial, format="xyz")
    write(root / "replica-04.xyz", final, format="xyz")
    launch(executable, root, "cp2k.inp", "cp2k.out", args.ranks)
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
