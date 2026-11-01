"""用法：python3 postprocess.py；检查完整受力与实际 HF 交换能，输出 eV 和 eV/Å。"""

import json
import re
import subprocess
import sys
from pathlib import Path


def main():
    root = Path.cwd()
    result = {}
    for name in ["pbe", "pbe0"]:
        subprocess.run(
            [sys.executable, str(root / "check_cp2k.py")], cwd=name, check=True
        )
        result[name] = json.loads((root / name / "results.json").read_text())
    text = (root / "pbe0/cp2k.out").read_text(errors="replace")
    values = re.findall(
        r"(?im)^.*Hartree.Fock.*exchange.*?([-+]?\d+\.\d+(?:[Ee][-+]?\d+)?)\s*$", text
    )
    if not values or abs(float(values[-1])) < 1e-6:
        raise SystemExit("未找到实际非零 HF 交换能，请核对 Libint 与输入")
    result["HF_exchange_energy_Hartree"] = float(values[-1])
    Path("hybrid-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
