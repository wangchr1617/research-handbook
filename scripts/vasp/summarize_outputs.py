"""汇总子目录的 VASP 输出。用法：python summarize_outputs.py ROOT -o results.csv。

能量取 energy(sigma->0)，单位 eV；体积单位 Å³。--natoms 可覆盖 OUTCAR 原子数。
作者：crwang；整合原 energy/volume/eentro/irreducible/check 系列脚本。
"""

import argparse
import csv
import re
import sys
from pathlib import Path

NUMBER = r"[-+]?\d*\.?\d+(?:[EeDd][-+]?\d+)?"


def last_number(text, pattern):
    matches = re.findall(pattern, text, re.I)
    return float(matches[-1].replace("D", "E").replace("d", "e")) if matches else None


def summarize(directory, natoms=None):
    """缺少的数值留空；存在 OSZICAR 不等于计算已完成。"""
    text = (directory / "OUTCAR").read_text(errors="replace")
    energy = last_number(text, rf"energy\(sigma->0\)\s*=\s*({NUMBER})")
    count = natoms or last_number(text, r"NIONS\s*=\s*(\d+)")
    oszicar = directory / "OSZICAR"
    ionic = ""
    if oszicar.exists():
        steps = [
            line.strip()
            for line in oszicar.read_text(errors="replace").splitlines()
            if "E0=" in line or "F=" in line
        ]
        ionic = steps[-1] if steps else ""
    return {
        "directory": str(directory),
        "energy_eV": energy,
        "energy_per_atom_eV": energy / count if energy is not None and count else None,
        "volume_A3": last_number(text, rf"volume of cell\s*:\s*({NUMBER})"),
        "entropy_eV": last_number(text, rf"EENTRO\s*=\s*({NUMBER})"),
        "irreducible_kpoints": last_number(text, r"(\d+)\s+irreducible k-points"),
        "natoms": count,
        "finished": "General timing and accounting" in text,
        "ionic_converged": "reached required accuracy" in text,
        "last_ionic_step": ionic,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("-o", "--output", type=Path, help="默认写到标准输出")
    parser.add_argument("--recursive", action="store_true", help="递归搜索 OUTCAR")
    parser.add_argument("--natoms", type=int, help="每原子能量的原子数，默认读取 NIONS")
    args = parser.parse_args()
    if args.natoms is not None and args.natoms <= 0:
        parser.error("--natoms 必须大于零")
    files = sorted(
        args.root.rglob("OUTCAR") if args.recursive else args.root.glob("*/OUTCAR")
    )
    if (args.root / "OUTCAR").is_file():
        files.insert(0, args.root / "OUTCAR")
    if not files:
        parser.error("未找到 OUTCAR")
    rows = [summarize(file.parent, args.natoms) for file in files]
    stream = (
        args.output.open("w", newline="", encoding="utf-8")
        if args.output
        else sys.stdout
    )
    try:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.output:
            stream.close()


if __name__ == "__main__":
    main()
