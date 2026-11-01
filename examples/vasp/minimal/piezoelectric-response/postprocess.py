"""用法：python3 postprocess.py；检查 ZnS 的电子/离子压电张量，单位 C/m²。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ORDER = [0, 1, 2, 4, 5, 3]  # VASP: xx yy zz xy yz zx → 常用 Voigt: xx yy zz yz xz xy。


def read_tensor(text, title):
    start = text.find(title)
    if start < 0:
        raise SystemExit(f"缺少张量：{title}")
    rows = []
    for line in text[start:].splitlines()[1:]:
        values = line.split()
        if len(values) == 7 and values[0] in ["x", "y", "z"]:
            rows.append(list(map(float, values[1:])))
        if len(rows) == 3:
            return np.array(rows)[:, ORDER]
    raise SystemExit("压电张量行数不完整")


def check_cubic(tensor):
    expected = np.zeros((3, 6))
    components = tensor[[0, 1, 2], [3, 4, 5]]
    expected[[0, 1, 2], [3, 4, 5]] = components.mean()
    if (
        not np.isfinite(tensor).all()
        or np.max(np.abs(tensor - expected)) > 5e-4
        or abs(components.mean()) < 0.01
    ):
        raise SystemExit("非零压电响应或 Td 对称性检查失败")


def main():
    subprocess.run([sys.executable, "check_vasp.py"], check=True)
    text = Path("OUTCAR").read_text(errors="replace")
    electronic = read_tensor(
        text,
        "PIEZOELECTRIC TENSOR (including local field effects)  for field in x, y, z        (C/m^2)",
    )
    ionic = read_tensor(
        text, "PIEZOELECTRIC TENSOR IONIC CONTR  for field in x, y, z        (C/m^2)"
    )
    total = electronic + ionic
    for t in [electronic, ionic, total]:
        check_cubic(t)
    frequencies = [
        float(v) for v in re.findall(r"\d+\s+f\s*=\s*([-+0-9.]+)\s+THz", text)
    ]
    if len([v for v in frequencies if v > 1]) != 3:
        raise SystemExit("ZnS 三个光学模式检查失败")
    result = {
        "voigt_order": ["xx", "yy", "zz", "yz", "xz", "xy"],
        "electronic_C_m2": electronic.tolist(),
        "ionic_C_m2": ionic.tolist(),
        "total_C_m2": total.tolist(),
        "e14_C_m2": float(total[0, 3]),
        "optical_frequencies_THz": [v for v in frequencies if v > 1],
    }
    Path("piezo-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
