"""用 Multiwfn 切换 CP2K SCF 或任务类型，默认写新文件。

用法：python diag2ot_geo2cell2md.py input.inp ot -o input-ot.inp
模式：ot、diagonalization、geo-opt、cell-opt、md；依赖命令 Multiwfn。
"""

import argparse
import subprocess
import tempfile
from pathlib import Path

from cp2k_sections import replace_section, section, set_keyword

CHOICES = {
    "ot": "4",
    "diagonalization": "\n",
    "geo-opt": "-1\n3",
    "cell-opt": "-1\n4",
    "md": "-1\n6\n10\n2",
}


def convert(source, mode, executable):
    target = source.read_text()
    with tempfile.TemporaryDirectory(prefix="cp2k-multiwfn-") as folder:
        commands = f"{source.resolve()}\ncp2k\ntemp.inp\n{CHOICES[mode]}\n0\nq\n"
        subprocess.run([executable], cwd=folder, input=commands, text=True, check=True)
        generated = (Path(folder) / "temp.inp").read_text()
    path = (
        ("FORCE_EVAL", "DFT", "SCF")
        if mode in ("ot", "diagonalization")
        else ("MOTION",)
    )
    target = replace_section(target, path, section(generated, path))
    if mode not in ("ot", "diagonalization"):
        target = set_keyword(
            target, ("GLOBAL",), "RUN_TYPE", mode.replace("-", "_").upper()
        )
        target = set_keyword(
            target,
            ("FORCE_EVAL",),
            "STRESS_TENSOR",
            "ANALYTICAL" if mode == "cell-opt" else None,
        )
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("mode", choices=CHOICES)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--executable", default="Multiwfn")
    args = parser.parse_args()
    output = args.output or args.input.with_suffix(f".{args.mode}.inp")
    if output.exists():
        parser.error("输出文件已存在")
    try:
        output.write_text(convert(args.input, args.mode, args.executable))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"错误：{error}\n")


if __name__ == "__main__":
    main()
