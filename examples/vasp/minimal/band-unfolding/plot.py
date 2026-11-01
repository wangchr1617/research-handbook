"""用法：python3 plot.py；使用 easyunfold 原生绘图，能量零点取超胞价带顶。"""

import json
import os
import subprocess
from pathlib import Path

SMEARING_EV = 0.03  # 图示能量展宽，eV；不改变原始谱权重。


def main():
    result = json.loads(Path("unfolding-results.json").read_text())
    executable = os.environ.get("EASYUNFOLD_EXEC", "easyunfold")
    subprocess.run(
        [
            executable,
            "unfold",
            "plot",
            "--eref",
            str(result["supercell_vbm_eV"]),
            "--emin",
            "-8",
            "--emax",
            "5",
            "--sigma",
            str(SMEARING_EV),
            "--npoints",
            "1200",
            "--dpi",
            "240",
            "--height",
            "4.5",
            "--width",
            "6",
            "--cmap",
            "Blues",
            "--title",
            "Si | pristine supercell unfolding",
            "-o",
            "si-unfolded.png",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
