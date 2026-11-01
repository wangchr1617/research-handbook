"""用法：python3 analyze.py；在 VASP 完成后调用 VASPKIT，检查关键输出。"""

import os
import re
import subprocess
import sys
from pathlib import Path

OUTPUTS = ["ABSORPTION.dat", "REFRACTIVE.dat"]


def main():
    executable = os.environ.get(
        "VASPKIT_EXEC", "vaspkit"
    )  # 可填写 VASPKIT 的绝对路径。
    with Path("vaspkit.in").open() as commands, Path("vaspkit.log").open("w") as log:
        subprocess.run(
            [executable],
            stdin=commands,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    log_text = Path("vaspkit.log").read_text(errors="replace")
    if re.search(r"forrtl:|severe \(|Error:", log_text, re.IGNORECASE):
        raise SystemExit("VASPKIT 报错，请检查 vaspkit.log")
    for name in OUTPUTS:
        path = Path(name)
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"缺少 {name}，请查看 vaspkit.log")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print("VASPKIT 输出：" + "、".join(OUTPUTS))


if __name__ == "__main__":
    main()
