"""读取本例 GW 输出；不把后自洽阶段的一次对角化误判为 SCF 不收敛。"""

import re
import subprocess
import sys
from pathlib import Path

import numpy as np


def qp_table():
    text = Path("gw/OUTCAR").read_text(errors="replace")
    blocks = text.split("QP shifts <psi_nk| G(iteration)W_0 |psi_nk>: iteration")[1:]
    if len(blocks) != 1:
        raise SystemExit("不是预期的一组单次 GW 输出，请核对 LSPECTRAL/NELMGW")
    rows = []
    kindex = None
    for line in blocks[0].splitlines():
        match = re.match(r"\s*k-point\s+(\d+)\s*:", line)
        if match:
            kindex = int(match[1])
            continue
        values = line.split()
        if kindex is not None and len(values) == 9 and values[0].isdigit():
            rows.append([kindex] + [float(x) for x in values])
    a = np.array(rows)
    if (
        a.shape != (32, 10)
        or not np.isfinite(a).all()
        or not np.all((a[:, 7] > 0) & (a[:, 7] < 1.5))
    ):
        raise SystemExit("本例 QP 表、Z 因子或能带数异常")
    return a


def completed(stage):
    if stage == "scf":
        subprocess.run(
            [sys.executable, str(Path.cwd() / "check_vasp.py")], cwd=stage, check=True
        )
    if "General timing and accounting" not in Path(stage, "OUTCAR").read_text(
        errors="replace"
    ):
        raise SystemExit(f"{stage} 未正常结束")
