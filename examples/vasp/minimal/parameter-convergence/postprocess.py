"""用法：python3 postprocess.py；检查各扫描计算，按最后两点的每原子能量差判断。"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from run import CUTOFFS_EV, K_MESHES

ENERGY_TOLERANCE_EV_ATOM = (
    0.001  # 演示用能量阈值，按研究目标调整；不代表力和应力已收敛。
)


def read_point(cutoff, mesh):
    directory = Path(f"encut-{cutoff}-k-{mesh}")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("check_vasp.py"))],
        cwd=directory,
        check=True,
    )
    tree = ET.parse(directory / "vasprun.xml")
    energy = float(
        tree.findall("calculation")[-1].find("energy/i[@name='e_0_energy']").text
    )
    natom = int(tree.find("atominfo/atoms").text)
    return {"cutoff_eV": cutoff, "k_mesh": mesh, "energy_eV_atom": energy / natom}


def main():
    cutoff_points = [read_point(cutoff, 7) for cutoff in CUTOFFS_EV]
    k_points = [read_point(450, mesh) for mesh in K_MESHES]
    output = {
        "cutoff_points": cutoff_points,
        "k_points": k_points,
        "threshold_eV_atom": ENERGY_TOLERANCE_EV_ATOM,
    }
    for name, points in [("cutoff", cutoff_points), ("k_mesh", k_points)]:
        change = abs(points[-1]["energy_eV_atom"] - points[-2]["energy_eV_atom"])
        output[name + "_last_change_eV_atom"] = change
        output[name + "_criterion_met"] = change < ENERGY_TOLERANCE_EV_ATOM
    Path("convergence-results.json").write_text(json.dumps(output, indent=2) + "\n")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(output, indent=2))
    if not output["cutoff_criterion_met"] or not output["k_mesh_criterion_met"]:
        raise SystemExit("最后两点未满足所设能量阈值，请继续扩大扫描")


if __name__ == "__main__":
    main()
