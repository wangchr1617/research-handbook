"""用法：python3 postprocess.py；检查SCF与最终磁态，提取能量和局域磁矩。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HARTREE_EV = 27.211386245988
result = {}
for stage in json.loads(Path("stages.json").read_text()):
    text = (Path(stage) / "openmx.out").read_text()
    summary = (Path(stage) / "system.out").read_text()
    if "The calculation was normally finished." not in text:
        raise SystemExit(f"{stage}未正常结束")
    changes = [float(x) for x in re.findall(r"dUele\s*=\s*([\d.Ee+-]+)", text)]
    # OpenMX以电子能量变化判定此处SCF，NormRD另作为诊断保存。
    threshold = float(
        re.search(
            r"scf.criterion\s+(\S+)", Path(stage + ".dat").read_text(), re.IGNORECASE
        )[1]
    )
    if not changes or changes[-1] > threshold * 1.05:
        raise SystemExit(f"{stage}电子迭代未达标准")
    energy = float(re.findall(r"Utot\.\s+(-?[\d.]+)", summary)[-1])
    moment = float(re.findall(r"Total spin moment \(muB\)\s+(-?[\d.]+)", summary)[-1])
    section = summary.rsplit("Total spin moment (muB)", 1)[-1].split("Sum of MulP:")[0]
    atoms = re.findall(r"^\s*\d+\s+(?:Fe|Ni|O)\s+([\d. -]+)$", section, re.MULTILINE)
    local = [float(row.split()[3]) for row in atoms]
    residual = float(re.findall(r"NormRD\s*=\s*([\d.Ee+-]+)", text)[-1])
    result[stage] = {
        "energy_hartree": energy,
        "total_spin_muB": moment,
        "local_spin_muB": local,
        "last_dUele_hartree": changes[-1],
        "density_residual": residual,
    }
if (
    len(result["afm"]["local_spin_muB"]) != 2
    or np.prod(result["afm"]["local_spin_muB"]) >= 0
):
    raise SystemExit("AFM初态未保持反平行局域磁矩")
result["AFM_minus_FM_eV_cell"] = (
    result["afm"]["energy_hartree"] - result["fm"]["energy_hartree"]
) * HARTREE_EV
fig, axs = plt.subplots(1, 2, figsize=(8, 3.7), layout="constrained")
axs[0].bar(["FM", "AFM"], [0, result["AFM_minus_FM_eV_cell"]])
axs[0].set(ylabel="Energy above FM (eV/2 Fe)")
for name, offset in [("fm", -0.17), ("afm", 0.17)]:
    axs[1].bar(
        np.arange(2) + offset,
        result[name]["local_spin_muB"],
        width=0.34,
        label=name.upper(),
    )
axs[1].set(xticks=[0, 1], xticklabels=["Fe1", "Fe2"], ylabel="Local Mulliken spin (μB)")
axs[1].legend()
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
