"""运行：python3 postprocess.py；提取 CP2K 能量与收敛标记（能量单位 Hartree）。"""

import json
import re
import subprocess
import sys
from pathlib import Path


def main():
    text = Path("cp2k.out").read_text(errors="replace")
    energies = re.findall(
        r"ENERGY\| Total FORCE_EVAL.*?energy.*?\s+([-+0-9.Ee]+)\s*$", text, re.MULTILINE
    )
    result = {
        "energy_Hartree": float(energies[-1]) if energies else None,
        "energy_evaluations": len(energies),
        "scf_converged": "SCF run converged" in text,
        "optimization_converged": "GEOMETRY OPTIMIZATION COMPLETED" in text
        or "CELL OPTIMIZATION COMPLETED" in text,
        "completed": "PROGRAM ENDED AT" in text,
    }
    if not result["optimization_converged"]:
        raise SystemExit("结构优化尚未收敛，请检查优化步数和受力/压力")
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["completed"] or not energies or "SCF run NOT converged" in text:
        raise SystemExit("计算未正常完成，请检查输出")

    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )


if __name__ == "__main__":
    main()
