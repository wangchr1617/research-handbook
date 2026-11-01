"""用法：python3 analyze.py；在 VASP 完成后调用 VASPKIT，检查关键输出。"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

OUTPUTS = ["ELASTIC_TENSOR"]


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
    stiffness = np.loadtxt("ELASTIC_TENSOR", skiprows=1)
    if stiffness.shape != (6, 6) or not np.isfinite(stiffness).all():
        raise SystemExit("弹性矩阵不完整或含非有限值")
    # 从 OUTCAR 核对单位和分量顺序：原始顺序 xx,yy,zz,xy,yz,zx。
    text = Path("OUTCAR").read_text(errors="replace")
    if "TOTAL ELASTIC MODULI (kBar)" not in text:
        raise SystemExit("缺少包含离子弛豫贡献的总弹性矩阵")
    rows = []
    for line in text.rsplit("TOTAL ELASTIC MODULI (kBar)", 1)[1].splitlines():
        parts = line.split()
        if len(parts) == 7 and parts[0] in ("XX", "YY", "ZZ", "XY", "YZ", "ZX"):
            rows.append(list(map(float, parts[1:])))
        if len(rows) == 6:
            break
    raw = np.array(rows)
    if raw.shape != (6, 6):
        raise SystemExit("OUTCAR 弹性矩阵不完整")
    order = [0, 1, 2, 4, 5, 3]  # 转为常用 Voigt 顺序 xx,yy,zz,yz,xz,xy。
    expected = raw[np.ix_(order, order)] * 0.1  # kBar → GPa
    if not np.allclose(stiffness, expected, atol=1e-3):
        raise SystemExit("VASPKIT 与 OUTCAR 的弹性分量或单位不一致")
    symmetric = bool(np.allclose(stiffness, stiffness.T, atol=1e-3))
    eigenvalues = np.linalg.eigvalsh(stiffness)
    c11, c12, c44 = stiffness[0, 0], stiffness[0, 1], stiffness[3, 3]
    cubic = np.zeros((6, 6))
    cubic[:3, :3] = c12
    np.fill_diagonal(cubic[:3, :3], c11)
    cubic[3:, 3:] = np.eye(3) * c44
    checks = {
        "symmetric": symmetric,
        "cubic_symmetry": bool(np.allclose(stiffness, cubic, atol=1e-3)),
        "positive_definite": bool(eigenvalues.min() > 0),
    }
    # 以下 VRH 公式针对本例立方硅，不能直接套用到任意晶系。
    bulk = (c11 + 2 * c12) / 3
    shear_voigt = (c11 - c12 + 3 * c44) / 5
    shear_reuss = 5 * (c11 - c12) * c44 / (4 * c44 + 3 * (c11 - c12))
    shear = (shear_voigt + shear_reuss) / 2
    young = 9 * bulk * shear / (3 * bulk + shear)
    poisson = (3 * bulk - 2 * shear) / (2 * (3 * bulk + shear))
    result = {
        "stiffness_GPa": stiffness.tolist(),
        "voigt_order": ["xx", "yy", "zz", "yz", "xz", "xy"],
        "eigenvalues_GPa": eigenvalues.tolist(),
        "bulk_GPa": float(bulk),
        "shear_Hill_GPa": float(shear),
        "young_Hill_GPa": float(young),
        "poisson_Hill": float(poisson),
        "checks": checks,
    }
    Path("elastic-results.json").write_text(json.dumps(result, indent=2) + "\n")
    if not all(checks.values()):
        raise SystemExit("本例硅的矩阵性质检查未通过")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
