"""用法：python3 postprocess.py；检查水分子的三个振动频率，单位 cm^-1。"""

import json
import re
import subprocess
import sys
from pathlib import Path


def main():
    text = Path("cp2k.out").read_text(errors="replace")
    lines = re.findall(r"^ VIB\|Frequency \(cm\^-1\)(.*)$", text, re.MULTILINE)
    frequencies = [float(value) for line in lines for value in line.split()]
    result = {
        "frequencies_cm-1": frequencies,
        "completed": "PROGRAM ENDED AT" in text,
    }
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    # 非线性三原子分子有三个内部振动，不把平动与转动当作振动峰。
    if (
        not result["completed"]
        or len(frequencies) != 3
        or min(frequencies) <= 0
        or "SCF run NOT converged" in text
    ):
        raise SystemExit("频率或收敛情况异常，请检查 cp2k.out")

    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )


if __name__ == "__main__":
    main()
