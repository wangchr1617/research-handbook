"""用法：python3 check_vasp.py；逐段检查 DFPT 自洽与线性响应迭代。"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    root = ET.parse("vasprun.xml").getroot()
    text = Path("OUTCAR").read_text(errors="replace")
    iterations = [
        int(n)
        for n in re.findall(
            r"^\s*(?:DAV|RMM|CG):\s*(\d+)", Path("OSZICAR").read_text(), re.MULTILINE
        )
    ]
    nelm = int(root.find(".//parameters//i[@name='NELM']").text)
    blocks = sum(n == 1 for n in iterations)
    # XML 汇总多个扰动；波函数导数预处理也不是独立 SCF，不按总行数或 EDIFF 条数推断。
    ground = text.split("Linear response reoptimize wavefunctions", 1)[0]
    if (
        not iterations
        or not blocks
        or max(iterations) >= nelm
        or "EDIFF is reached" not in ground
        or "Linear response finished" not in Path("OSZICAR").read_text()
        or "General timing and accounting" not in text
    ):
        raise SystemExit("DFPT 的自洽或响应迭代未正常收敛")
    result = {
        "response_blocks": blocks,
        "maximum_iterations_in_block": max(iterations),
        "EDIFF_markers": text.count("EDIFF is reached"),
        "completed": True,
    }
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
