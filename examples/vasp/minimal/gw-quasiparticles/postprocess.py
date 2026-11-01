"""用法：python3 postprocess.py；检查并保存四个不可约 k 点的准粒子能级。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from read_results import completed, qp_table


def main():
    for stage in ["scf", "exact", "gw"]:
        completed(stage)
    a = qp_table()
    occupied = a[:, 8] > 1
    empty = a[:, 8] < 1
    pbe = float(a[empty, 2].min() - a[occupied, 2].max())
    gw = float(a[empty, 3].min() - a[occupied, 3].max())
    if min(pbe, gw) <= 0:
        raise SystemExit("本例占据与带隙检查失败")
    result = {
        "sampled_pbe_gap_eV": pbe,
        "sampled_gw_gap_eV": gw,
        "min_Z": float(a[:, 7].min()),
        "max_Z": float(a[:, 7].max()),
        "qp_rows": len(a),
    }
    Path("gw-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    np.savetxt(
        "quasiparticles.dat",
        a,
        header="k band KS_eV QP_eV sigma Vxc Vx Z occupation ImSigma",
    )
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
