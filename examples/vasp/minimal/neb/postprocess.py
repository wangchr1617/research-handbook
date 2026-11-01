"""用法：python3 postprocess.py；检查 CI-NEB，调用 VTST nebbarrier.pl 提取路径能量并绘图。"""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from ase.io import read


def main():
    for image in ["01", "02", "03"]:
        text = (Path(image) / "OUTCAR").read_text(errors="replace")
        if "reached required accuracy" not in text:
            raise SystemExit(f"{image} 的 NEB 尚未收敛")
        before = read(Path(image) / "POSCAR", format="vasp")
        after = read(Path(image) / "CONTCAR", format="vasp")
        if not np.allclose(before.positions[1:], after.positions[1:], atol=1e-6):
            raise SystemExit(f"{image} 的固定原子发生移动")
        root = ET.parse(Path(image) / "vasprun.xml").getroot()
        steps = root.findall("calculation")
        if not steps or any(len(step.findall("scstep")) >= 120 for step in steps):
            raise SystemExit(f"{image} 的电子迭代需检查")
    executable = os.environ.get("NEBBARRIER_EXEC", "nebbarrier.pl")
    with Path("vtst-analysis.log").open("w") as log:
        subprocess.run([executable], stdout=log, stderr=subprocess.STDOUT, check=True)
    data = np.loadtxt("neb.dat")
    if data.shape != (5, 5) or not np.isfinite(data).all():
        raise SystemExit("neb.dat 的路径能量不完整")
    barrier = float(data[:, 2].max())
    if barrier <= 0:
        raise SystemExit("未找到相对初态的正势垒，请检查路径")
    result = {
        "barrier_eV": barrier,
        "endpoint_difference_eV": float(data[-1, 2]),
        "converged_images": 3,
    }
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
