"""用法：python3 postprocess.py；用 VTST 和 Bader 程序分析两组网格，检查电荷守恒并绘图。"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

GRID_TOLERANCE_E = 0.01  # 两组网格的净原子电荷允许变化，单位 e；不是通用精度标准。


def main():
    root = Path.cwd()
    zval = np.array(
        [
            float(value)
            for value in re.findall(
                r"ZVAL\s*=\s*([-+0-9.Ee]+)", (root / "POTCAR").read_text()
            )
        ]
    )
    if zval.shape != (2,):
        raise SystemExit("本例需按 Na_pv、Cl 顺序准备两套势")
    results = []
    for grid in [96, 144]:
        work = root / f"grid-{grid}"
        commands = [
            (
                [os.environ.get("CHGSUM_EXEC", "chgsum.pl"), "AECCAR0", "AECCAR2"],
                "chgsum.log",
            ),
            (
                [os.environ.get("BADER_EXEC", "bader"), "CHGCAR", "-ref", "CHGCAR_sum"],
                "bader.log",
            ),
        ]
        for command, name in commands:
            with (work / name).open("w") as log:
                subprocess.run(
                    command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
                )
        rows = [
            list(map(float, line.split()))
            for line in (work / "ACF.dat").read_text().splitlines()
            if re.match(r"^\s*\d+\s", line)
        ]
        data = np.array(rows)
        if data.shape != (2, 7) or not np.isfinite(data).all():
            raise SystemExit(f"{grid} 网格的原子分区结果不完整")
        electrons = data[:, 4]
        charge = zval - electrons
        if abs(electrons.sum() - zval.sum()) > 1e-3:
            raise SystemExit("价电子数不守恒，请检查参考密度和真空分区")
        if not (charge[0] > 0 and charge[1] < 0):
            raise SystemExit("NaCl 电荷转移方向异常，请检查势与元素顺序")
        results.append(
            {
                "grid": grid,
                "valence_electrons": electrons.tolist(),
                "net_charge_e": charge.tolist(),
            }
        )
    change = float(
        np.abs(np.array(results[1]["net_charge_e"]) - results[0]["net_charge_e"]).max()
    )
    Path("bader-results.json").write_text(
        json.dumps({"results": results, "max_grid_change_e": change}, indent=2) + "\n"
    )
    if change > GRID_TOLERANCE_E:
        raise SystemExit("原子电荷随网格变化仍较大，请继续加密")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(f"两组网格最大电荷变化：{change:.6f} e")


if __name__ == "__main__":
    main()
