"""用法：python3 analyze.py；读取静态电子介电张量和 Born 有效电荷，检查本例硅的对称性。"""

import json
import re
from pathlib import Path

import numpy as np


def main():
    text = Path("OUTCAR").read_text(errors="replace")
    marker = (
        "MACROSCOPIC STATIC DIELECTRIC TENSOR (including local field effects in DFT)"
    )
    if marker not in text:
        raise SystemExit("缺少包含局域场效应的电子介电张量")
    lines = text.rsplit(marker, 1)[1].splitlines()
    rows = []
    for line in lines:
        fields = line.split()
        if len(fields) == 3:
            try:
                rows.append(list(map(float, fields)))
            except ValueError:
                continue
        if len(rows) == 3:
            break
    epsilon = np.array(rows)
    if epsilon.shape != (3, 3) or not np.isfinite(epsilon).all():
        raise SystemExit("介电张量不完整或包含非有限值")
    born_marker = "BORN EFFECTIVE CHARGES (including local field effects)"
    if born_marker not in text:
        raise SystemExit("缺少 Born 有效电荷")
    blocks = re.findall(
        r"ion\s+\d+\s*\n((?:\s*[123]\s+[-+0-9.]+\s+[-+0-9.]+\s+[-+0-9.]+\s*\n){3})",
        text.rsplit(born_marker, 1)[1],
    )
    born = np.array(
        [
            [list(map(float, line.split()[1:])) for line in block.strip().splitlines()]
            for block in blocks
        ]
    )
    if born.shape != (2, 3, 3) or not np.isfinite(born).all():
        raise SystemExit("本例应有两个 Si 原子的 Born 有效电荷张量")
    # 下列检查针对立方金刚石硅，换体系时应按其对称性调整。
    isotropic = np.eye(3) * np.trace(epsilon) / 3
    checks = {
        "epsilon_symmetric": bool(np.allclose(epsilon, epsilon.T, atol=1e-5)),
        "epsilon_isotropic": bool(np.allclose(epsilon, isotropic, atol=1e-4)),
        "epsilon_eigenvalues_above_one": bool(np.linalg.eigvalsh(epsilon).min() > 1),
        "born_zero_for_silicon": bool(np.abs(born).max() < 1e-4),
        "born_acoustic_sum_rule": bool(np.abs(born.sum(axis=0)).max() < 1e-4),
    }
    result = {
        "ion_clamped_dielectric_tensor": epsilon.tolist(),
        "born_effective_charges_e": born.tolist(),
        "checks": checks,
    }
    Path("dielectric-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit("硅示例的响应性质检查未通过")


if __name__ == "__main__":
    main()
