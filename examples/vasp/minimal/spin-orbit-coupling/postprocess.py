"""用法：python3 postprocess.py；核对硅 Γ 点 SOC 价带分裂，输出 eV。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from read_eigen import read_eigen


def main():
    result = {}
    for stage in ["scalar", "soc"]:
        subprocess.run(
            [sys.executable, str(Path.cwd() / "check_vasp.py")], cwd=stage, check=True
        )
        k, values, parameters = read_eigen(stage)
        gamma = np.flatnonzero(np.linalg.norm(k, axis=1) < 1e-8)
        if len(gamma) != 1 or values.shape[0] != 1:
            raise SystemExit("非共线数据或 Γ 点布局异常")
        if parameters.get("LSORBIT") != ("T" if stage == "soc" else "F"):
            raise SystemExit("SOC 开关未实际生效")
        e = values[0, gamma[0], :, 0]
        p_like = e[2:8]
        if not np.isfinite(e).all():
            raise SystemExit("非有限本征值")
        result[stage] = {
            "gamma_valence_eigenvalues_eV": e[:8].tolist(),
            "p_valence_spread_eV": float(np.ptp(p_like)),
            "split_off_eV": float(e[4] - e[3]),
        }
    if (
        result["scalar"]["p_valence_spread_eV"] > 1e-3
        or not 0.005 < result["soc"]["split_off_eV"] < 0.2
    ):
        raise SystemExit("未恢复无 SOC 简并或未观察到合理 SOC 分裂")
    Path("soc-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
