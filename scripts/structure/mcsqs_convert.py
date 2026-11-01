"""批量转换 ATAT SQS 输出。用法：python mcsqs_convert.py 'bestsqs*.out' --format vasp --output-dir structures。

依赖 ATAT 的 str2cif / sqs2poscar；在临时目录执行，不移动或修改原始 SQS 文件。
"""

import argparse
import glob
import shutil
import subprocess
import tempfile
from pathlib import Path


def convert(source, fmt, executable):
    with tempfile.TemporaryDirectory(prefix="sqs-convert-") as folder:
        work = Path(folder)
        local = work / source.name
        shutil.copy2(source, local)
        if fmt == "cif":
            with local.open() as stream:
                return subprocess.run(
                    [executable],
                    cwd=work,
                    stdin=stream,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
        subprocess.run([executable, local.name], cwd=work, check=True)
        lines = (work / (local.name + "-POSCAR")).read_text().splitlines()
        if len(lines) < 8:
            raise ValueError("sqs2poscar 输出不完整")
        # 仅修复旧版转换器写在缩放因子行的 xxx，不改动其他文本。
        if lines[1].strip() == "xxx":
            lines[1] = "1.0"
        return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern", help="输入文件模式，加引号以保留通配符")
    parser.add_argument("--format", choices=["vasp", "cif"], required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--executable", help="默认 sqs2poscar 或 str2cif")
    args = parser.parse_args()
    sources = [
        Path(name).resolve()
        for name in sorted(glob.glob(args.pattern))
        if Path(name).is_file()
    ]
    if not sources or len({p.stem for p in sources}) != len(sources):
        parser.error("未找到文件，或输出文件名存在冲突")
    suffix = ".vasp" if args.format == "vasp" else ".cif"
    if any((args.output_dir / (p.stem + suffix)).exists() for p in sources):
        parser.error("输出文件已存在")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    executable = args.executable or (
        "sqs2poscar" if args.format == "vasp" else "str2cif"
    )
    for source in sources:
        text = convert(source, args.format, executable)
        if not text.strip():
            parser.exit(1, f"{source} 未产生输出\n")
        (args.output_dir / (source.stem + suffix)).write_text(text)


if __name__ == "__main__":
    main()
