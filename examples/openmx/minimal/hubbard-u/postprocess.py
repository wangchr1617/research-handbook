"""用法：python3 postprocess.py；检查SCF与最终磁态，提取能量和局域磁矩。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
for stage in ["u0", "u4"]:
    if "Occupation Number in LDA+U" not in (Path(stage) / "system.out").read_text():
        raise SystemExit("缺少DFT+U占据矩阵输出")
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.bar(["U=0", "U=4 eV"], [result[s]["local_spin_muB"][0] for s in ["u0", "u4"]])
ax.set(ylabel="Ni local Mulliken spin (μB)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
