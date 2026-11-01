"""用法：python3 postprocess.py；检查 VASP 输出，再用 BoltzTraP2 插值和积分。"""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.units import Hartree, Rydberg
from BoltzTraP2.serialization import load_results

INTERPOLATION_MULTIPLIER = 3  # 插值点增密系数；正式研究需检查插值收敛。
TEMPERATURES = "300,600"  # 积分温度，单位 K。
DOS_BINS = 1000  # 积分用 DOS 网格数。
ENERGY_WINDOW_EV = 1.5  # 本例检查和绘图的化学势窗口，相对电中性参考能量。


def main():
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("check_vasp.py"))], check=True
    )
    executable = os.environ.get("BTP2_EXEC", "btp2")
    commands = [
        (
            [
                executable,
                "-n",
                "1",
                "interpolate",
                "-m",
                str(INTERPOLATION_MULTIPLIER),
                ".",
            ],
            "interpolate.log",
        ),
        (
            [
                executable,
                "-n",
                "1",
                "integrate",
                "-b",
                str(DOS_BINS),
                "interpolation.bt2",
                TEMPERATURES,
            ],
            "integrate.log",
        ),
    ]
    for command, name in commands:
        with Path(name).open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    result = load_results("interpolation.btj")
    reference = float(result[1] * Hartree)
    table = np.loadtxt("interpolation.trace")
    mask = np.abs(table[:, 0] * Rydberg - reference) <= ENERGY_WINDOW_EV
    selected = table[mask]
    if (
        selected.shape[0] < 10
        or selected.shape[1] != 10
        or not np.isfinite(selected).all()
    ):
        raise SystemExit("输运表格不完整或目标窗口含非有限值")
    if (
        not np.allclose(
            np.unique(selected[:, 1]),
            sorted(float(value) for value in TEMPERATURES.split(",")),
        )
        or (selected[:, [5, 7]] < 0).any()
    ):
        raise SystemExit("温度或纵向输运系数异常")
    metadata = result[-1]
    if metadata.get("scattering_model") != "uniform_tau":
        raise SystemExit("本例仅处理常数弛豫时间近似")
    metrics = {
        "reference_energy_eV": reference,
        "temperatures_K": np.unique(selected[:, 1]).tolist(),
        "rows_in_window": len(selected),
        "scattering_model": metadata["scattering_model"],
        "boltztrap2_version": metadata["program_version"],
        "energy_window_eV": ENERGY_WINDOW_EV,
    }
    Path("transport-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
