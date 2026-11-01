"""用法：python3 postprocess.py；检查两侧真空势平台并计算功函数，单位 eV。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.calculators.vasp import VaspChargeDensity

VACUUM_WINDOW_A = 2.0  # 两端各取该宽度作平台检查，远离表面。


def main():
    subprocess.run([sys.executable, "check_vasp.py"], check=True)
    grid = VaspChargeDensity("LOCPOT")
    atoms = grid.atoms[0]
    # ASE 的密度读入器会除以体积；LOCPOT 是势，乘回体积恢复 eV。
    potential = grid.chg[0] * atoms.get_volume()
    average = potential.mean(axis=(0, 1))
    length = atoms.cell.lengths()[2]
    z = np.arange(len(average)) * length / len(average)
    lower = z < VACUUM_WINDOW_A
    upper = z > length - VACUUM_WINDOW_A
    if (
        not np.isfinite(average).all()
        or max(np.ptp(average[lower]), np.ptp(average[upper])) > 0.05
    ):
        raise SystemExit("真空势尚未形成平坦平台")
    vac = [float(average[mask].mean()) for mask in [lower, upper]]
    if abs(vac[0] - vac[1]) > 0.05:
        raise SystemExit("对称slab两侧真空势不一致")
    out = Path("OUTCAR").read_text(errors="replace")
    values = re.findall(r"Fermi energy:\s*([-+0-9.Ee]+)", out)
    if not values:
        values = re.findall(r"E-fermi\s*:\s*([-+0-9.Ee]+)", out)
    ef = float(values[-1])
    native = re.findall(
        r"vacuum level on the upper side and lower side of the slab\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)",
        out,
    )
    if native and not np.allclose(list(map(float, native[-1])), vac[::-1], atol=0.005):
        raise SystemExit("网格积分与 VASP 原生真空势不一致")
    work = [v - ef for v in vac]
    if not all(1 < x < 8 for x in work):
        raise SystemExit("功函数异常，请检查势与费米能参考")
    result = {
        "fermi_eV": ef,
        "vacuum_levels_eV": vac,
        "work_functions_eV": work,
        "vacuum_window_A": VACUUM_WINDOW_A,
        "grid_shape": list(potential.shape),
    }
    Path("work-function-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    np.savetxt(
        "potential-profile.dat",
        np.column_stack([z, average]),
        header="z_A electrostatic_potential_eV",
    )
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
