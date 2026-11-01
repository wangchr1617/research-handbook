"""用法：python3 postprocess.py；检查 CP2K NEB 收敛，提取路径势垒并绘图。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read
from ase.units import Bohr, Hartree


def main():
    text = Path("cp2k.out").read_text(errors="replace")
    if "Band task converged" not in text or "PROGRAM ENDED AT" not in text:
        raise SystemExit("NEB 未收敛或程序未正常结束，请检查 cp2k.out")
    reference = read("replica-00.xyz")
    for index in range(1, 6):
        replica = Path(f"neb-BAND{index}.out").read_text(errors="replace")
        if "SCF run NOT converged" in replica or "SCF run converged" not in replica:
            raise SystemExit(f"副本 {index} 的 SCF 未通过检查")
        final = read(f"neb-pos-Replica_nr_{index}-1.xyz", index=-1)
        if not np.allclose(reference.positions[1:], final.positions[1:], atol=1e-6):
            raise SystemExit(f"副本 {index} 的固定原子发生移动")
    values = np.atleast_2d(np.loadtxt("neb-1.ener"))[-1]
    if values.size != 10 or not np.isfinite(values).all():
        raise SystemExit("本例需要完整的五副本能量与四段距离")
    # CP2K BAND 能量是 Hartree，副本间距离是 Bohr。
    energies = (values[1:6] - values[1]) * Hartree
    distances = np.r_[0, np.cumsum(values[6:])] * Bohr
    profile = np.column_stack([np.arange(5), distances, energies])
    np.savetxt(
        "neb-profile.dat", profile, header="Image Distance(A) Relative_energy(eV)"
    )
    barrier = float(energies.max())
    if barrier <= 0:
        raise SystemExit("未找到正势垒，请检查路径")
    result = {
        "barrier_eV": barrier,
        "endpoint_difference_eV": float(energies[-1]),
        "converged_replicas": 5,
        "fixed_atoms_checked": 6,
    }
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
