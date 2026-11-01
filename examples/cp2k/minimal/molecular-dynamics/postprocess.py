"""运行：python3 postprocess.py；提取 CP2K 能量与收敛标记（能量单位 Hartree）。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np


def main():
    text = Path("cp2k.out").read_text(errors="replace")
    energies = re.findall(
        r"ENERGY\| Total FORCE_EVAL.*?energy.*?\s+([-+0-9.Ee]+)\s*$", text, re.MULTILINE
    )
    files = list(Path(".").glob("*-1.ener"))
    if len(files) != 1:
        raise SystemExit("需要唯一的 MD 能量记录")
    values = np.loadtxt(files[0], ndmin=2)
    incar = Path("cp2k.inp").read_text()
    expected = int(
        re.search(r"^\s*STEPS\s+(\d+)", incar, re.MULTILINE | re.IGNORECASE).group(1)
    )
    timestep = float(
        re.search(
            r"^\s*TIMESTEP\s+([0-9.]+)", incar, re.MULTILINE | re.IGNORECASE
        ).group(1)
    )
    if (
        not np.isfinite(values).all()
        or not np.array_equal(values[:, 0], np.arange(expected + 1))
        or not np.allclose(values[:, 1], values[:, 0] * timestep)
    ):
        raise SystemExit("MD 步数、时间轴或数值异常")
    result = {
        "md_steps": expected,
        "final_time_fs": float(values[-1, 1]),
        "energy_Hartree": float(energies[-1]) if energies else None,
        "energy_evaluations": len(energies),
        "scf_converged": "SCF run converged" in text,
        "optimization_converged": "GEOMETRY OPTIMIZATION COMPLETED" in text
        or "CELL OPTIMIZATION COMPLETED" in text,
        "completed": "PROGRAM ENDED AT" in text,
    }
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["completed"] or not energies or "SCF run NOT converged" in text:
        raise SystemExit("计算未正常完成，请检查输出")

    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )


if __name__ == "__main__":
    main()
