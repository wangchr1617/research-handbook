"""准备 VASP 批量任务；只生成输入，不提交作业。

用法：python prepare_jobs.py encut 300 400 500 --source . --output encut-test
      python prepare_jobs.py scale 0.95 1.0 1.05 --source . --output ev-test
      python prepare_jobs.py structures 'POSCAR-0*' --output phonons
      python prepare_jobs.py kpoints calculations --spacing 0.04
"""

import argparse
import math
import re
import shutil
import subprocess
from pathlib import Path


def copy_inputs(source, target):
    required = [source / name for name in ("INCAR", "POSCAR", "POTCAR")]
    if not all(p.is_file() for p in required):
        raise ValueError(f"{source} 缺少 INCAR、POSCAR 或 POTCAR")
    target.mkdir(parents=True)  # 已有任务目录报错，不删除旧计算。
    for file in required + list(source.glob("*.pbs")):
        shutil.copy2(file, target / file.name)
    if (source / "KPOINTS").exists():
        shutil.copy2(source / "KPOINTS", target / "KPOINTS")


def prepare_parameter(source, output, values, mode):
    if any(not math.isfinite(value) or value <= 0 for value in values) or len(
        set(values)
    ) != len(values):
        raise ValueError("参数必须为互不重复的正数")
    targets = [output / f"{value:g}" for value in values]
    if len(set(targets)) != len(targets) or any(
        target.exists() or target.is_symlink() for target in targets
    ):
        raise FileExistsError("输出任务目录已存在")
    for value, target in zip(values, targets):
        copy_inputs(source, target)
        if mode == "encut":
            path = target / "INCAR"
            text = path.read_text()
            # 同时支持同一行分号分隔的 INCAR 参数，清除旧 ENCUT 后写入新值。
            text = re.sub(r"(?im)(^|;)\s*ENCUT\s*=[^;\n]*", r"\1", text)
            path.write_text(text.rstrip() + f"\nENCUT = {value:g}\n")
        else:
            from ase.io import read, write

            atoms = read(source / "POSCAR", format="vasp")
            atoms.set_cell(atoms.cell * value, scale_atoms=True)
            write(target / "POSCAR", atoms, format="vasp", direct=True)


def prepare_structures(pattern, output):
    import glob

    sources = [
        Path(name) for name in sorted(glob.glob(pattern)) if Path(name).is_file()
    ]
    if not sources:
        raise ValueError("未匹配到结构文件")
    targets = [output / p.stem for p in sources]
    if len(set(targets)) != len(targets) or any(
        p.exists() or p.is_symlink() for p in targets
    ):
        raise FileExistsError("输出目录重名或已经存在")
    for source, target in zip(sources, targets):
        target.mkdir(parents=True)
        shutil.copy2(source, target / "POSCAR")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("encut", "scale"):
        cmd = sub.add_parser(mode)
        cmd.add_argument(
            "values", nargs="+", type=float, help="ENCUT/eV 或晶格线性缩放倍数"
        )
        cmd.add_argument("--source", type=Path, default=Path("."))
        cmd.add_argument("--output", type=Path, required=True)
    cmd = sub.add_parser("structures")
    cmd.add_argument("pattern", help="结构文件的 glob 模式，需加引号")
    cmd.add_argument("--output", type=Path, required=True)
    cmd = sub.add_parser("kpoints")
    cmd.add_argument("root", type=Path)
    cmd.add_argument(
        "--spacing", type=float, default=0.04, help="VASPKIT K 网格间距，单位 2π/Å"
    )
    cmd.add_argument("--executable", default="vaspkit")
    args = parser.parse_args()
    try:
        if args.mode in ("encut", "scale"):
            prepare_parameter(args.source, args.output, args.values, args.mode)
        elif args.mode == "structures":
            prepare_structures(args.pattern, args.output)
        else:
            if not math.isfinite(args.spacing) or args.spacing <= 0:
                parser.error("间距须大于零")
            inputs = sorted(args.root.glob("*/INCAR"))
            if not inputs:
                raise ValueError("未找到子目录 INCAR")
            for path in inputs:
                subprocess.run(
                    [args.executable],
                    cwd=path.parent,
                    input=f"102\n2\n{args.spacing}\n",
                    text=True,
                    check=True,
                )
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"错误：{error}\n")


if __name__ == "__main__":
    main()
