"""用法：python3 postprocess.py；检查原生ORCA结果，提取目标量与绘图。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
HARTREE_EV = 27.211386245988
texts = {}
energies = {}
for stage in json.loads(Path("stages.json").read_text()):
    text = (Path(stage) / "orca.out").read_text()
    if "ORCA TERMINATED NORMALLY" not in text or "SCF NOT CONVERGED" in text:
        raise SystemExit(f"{stage}未正常收敛")
    texts[stage] = text
    energies[stage] = float(
        re.findall(r"FINAL SINGLE POINT ENERGY\s+(-?[\d.]+)", text)[-1]
    )
result = {"energies_hartree": energies}
for text in texts.values():
    if int(re.findall(r"Number of Electrons\s+NEL\s+\.+\s+(\d+)", text)[-1]) != 18:
        raise SystemExit("未显式计算Ar的18个电子")
if "Relativistic Method            ... X2C" not in texts["x2c"]:
    raise SystemExit("未启用X2C")
result["x2c_minus_nonrel_hartree"] = energies["x2c"] - energies["nonrel"]
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
