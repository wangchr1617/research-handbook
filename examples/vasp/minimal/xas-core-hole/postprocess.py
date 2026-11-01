"""用法：python3 postprocess.py；检查 Si 核空穴计算并提取 OUTCAR 的 K 边谱。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d


def main():
    subprocess.run([sys.executable, "check_vasp.py"], check=True)
    out = Path("OUTCAR").read_text()
    nelect = float(re.search(r"NELECT\s*=\s*([0-9.]+)", out)[1])
    if nelect != 33 or "Ending Core_Hole_Spec" not in Path("vasp.log").read_text():
        raise SystemExit("请核对 XCH 电子数与核谱计算结束标记")
    block = out.split("frequency dependent IMAGINARY DIELECTRIC FUNCTION", 1)[1]
    rows = []
    for line in block.splitlines()[3:]:
        values = line.split()
        if len(values) != 7:
            if rows:
                break
            continue
        try:
            rows.append([float(v) for v in values])
        except ValueError:
            if rows:
                break
    data = np.asarray(rows)
    if data.shape != (2000, 7) or not np.isfinite(data).all():
        raise SystemExit("核谱网格不完整")
    energy = data[:, 0]
    raw = data[:, 1:4].mean(axis=1)
    if not (np.diff(energy) > 0).all() or raw.max() <= 0 or (raw > 0).sum() < 20:
        raise SystemExit("能量网格或谱强度异常")
    # 演示用高斯标准差，单位 eV；正式谱需按寿命和仪器分辨率选择展宽。
    sigma_eV = 0.5
    broadened = gaussian_filter1d(raw, sigma_eV / np.diff(energy).mean())
    np.savetxt(
        "xas-spectrum.dat",
        np.column_stack([energy, raw, broadened]),
        header="core_transition_energy_eV raw_mean_Im_eps gaussian_sigma_0.5eV",
    )
    metrics = {
        "NELECT": nelect,
        "points": len(data),
        "energy_interval_eV": [float(energy[0]), float(energy[-1])],
        "positive_points": int((raw > 0).sum()),
        "peak_eV": float(energy[broadened.argmax()]),
        "gaussian_sigma_eV": sigma_eV,
    }
    Path("xas-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
