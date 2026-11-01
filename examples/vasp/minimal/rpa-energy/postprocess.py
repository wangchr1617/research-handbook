"""用法：python3 postprocess.py；分开检查非自洽 HF 总能与 ACFDT-RPA 相关能。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from read_results import completed


def main():
    for stage in ["scf", "exact", "exx", "rpa"]:
        completed(stage)
    hf = float(
        re.findall(
            r"free\s+energy\s+TOTEN\s*=\s*([-+0-9.Ee]+)", Path("exx/OUTCAR").read_text()
        )[-1]
    )
    text = Path("rpa/OUTCAR").read_text()
    section = text.split("cutoff energy     smooth cutoff   RPA   correlation")[-1]
    rows = []
    for line in section.splitlines():
        values = line.split()
        if len(values) == 4:
            try:
                rows.append(list(map(float, values)))
            except ValueError:
                pass
        if "linear regression" in line:
            break
    a = np.array(rows)
    if a.shape != (8, 4) or not np.isfinite(a).all() or not np.all(a[:, 2] < 0):
        raise SystemExit("RPA 内部截断扫描表异常")
    correlation = float(a[0, 2])
    result = {
        "HF_total_energy_on_PBE_orbitals_eV": hf,
        "RPA_correlation_eV": correlation,
        "RPA_total_energy_eV": hf + correlation,
        "response_cutoff_eV": float(a[0, 0]),
        "rows": len(a),
    }
    Path("rpa-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    np.savetxt(
        "rpa-cutoffs.dat",
        a,
        header="ENCUTGW_eV smooth_cutoff_eV Ec_RPA_eV Hartree_MP2_eV",
    )
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
