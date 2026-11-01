"""用法：python3 postprocess.py；用 Multiwfn 相减密度，检查守恒并绘图。"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.calculators.vasp import VaspChargeDensity
from ase.io.cube import read_cube
from ase.units import Bohr


def main():
    densities = [
        VaspChargeDensity(f"{part}/CHGCAR") for part in ["combined", "na", "cl"]
    ]
    cell = densities[0].atoms[0].cell
    shape = densities[0].chg[0].shape
    for density in densities:
        if (
            not np.allclose(density.atoms[0].cell, cell, atol=1e-9)
            or density.chg[0].shape != shape
        ):
            raise SystemExit("晶胞或 FFT 网格不一致，不能直接相减")
    total = densities[0].atoms[0]
    for index in range(2):
        fragment = densities[index + 1].atoms[0]
        delta = (
            fragment.get_scaled_positions()[0]
            - total.get_scaled_positions()[index]
            + 0.5
        ) % 1 - 0.5
        if (
            len(fragment) != 1
            or fragment[0].symbol != total[index].symbol
            or np.linalg.norm(delta @ cell) > 1e-7
        ):
            raise SystemExit("参考片段的元素或位置与整体不一致")
    executable = os.environ.get("MULTIWFN_EXEC") or next(
        (
            name
            for name in ["Multiwfn", "Multiwfn_noGUI", "multiwfn"]
            if shutil.which(name)
        ),
        None,
    )
    if not executable:
        raise SystemExit("请安装 Multiwfn 或设置 MULTIWFN_EXEC")
    with Path("multiwfn.in").open() as commands, Path("multiwfn.log").open("w") as log:
        subprocess.run(
            [executable, "combined/CHGCAR"],
            stdin=commands,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    log_text = Path("multiwfn.log").read_text(errors="replace")
    if "cube file has been outputted" not in log_text or "Error:" in log_text:
        raise SystemExit("Multiwfn 未正常完成，请检查 multiwfn.log")
    with Path("cdd.cub").open() as stream:
        cube = read_cube(stream)
    # Multiwfn 用原子单位导出电子密度；ASE CHGCAR 读取结果为 e/Å³。
    data = cube["data"] / Bohr**3
    expected = densities[0].chg[0] - densities[1].chg[0] - densities[2].chg[0]
    if data.shape != shape or not np.allclose(data, expected, atol=5e-6, rtol=1e-4):
        raise SystemExit("Cube 与原始密度的差值不一致，请核对单位和交互输入")
    integral = float(data.mean() * total.get_volume())
    electrons = [
        float(density.chg[0].mean() * density.atoms[0].get_volume())
        for density in densities
    ]
    result = {
        "grid_shape": list(shape),
        "reference_electron_counts": electrons,
        "integral_e": integral,
        "minimum_e_A3": float(data.min()),
        "maximum_e_A3": float(data.max()),
    }
    Path("cdd-results.json").write_text(json.dumps(result, indent=2) + "\n")
    if (
        not np.isfinite(data).all()
        or abs(integral) > 1e-4
        or not (data.min() < 0 < data.max())
        or not np.allclose(electrons, [14, 7, 7], atol=1e-4)
    ):
        raise SystemExit("差分密度的电子数、符号或积分检查未通过")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
