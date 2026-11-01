"""用法：python3 postprocess.py；调用 Phonopy 生成色散与简谐热力学文件。"""

import json
import subprocess
import sys
from pathlib import Path

import yaml


def main():
    outputs = sorted(Path(".").glob("disp-*/vasprun.xml"))
    if not outputs:
        raise SystemExit("缺少位移结构的 vasprun.xml")
    commands = [
        ["phonopy-init", "-f", *map(str, outputs)],
        ["phonopy", "--config", "band.conf"],
        ["phonopy", "--config", "thermal.conf"],
    ]
    with Path("phonopy.log").open("w") as log:
        for command in commands:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    for name in ["band.yaml", "thermal_properties.yaml"]:
        if not Path(name).is_file():
            raise SystemExit(f"缺少 {name}，请检查 phonopy.log")
    band = yaml.safe_load(Path("band.yaml").read_text())
    thermal = yaml.safe_load(Path("thermal_properties.yaml").read_text())
    frequencies = [
        mode["frequency"] for point in band["phonon"] for mode in point["band"]
    ]
    result = {
        "minimum_frequency_THz": min(frequencies),
        "natom": thermal["natom"],
        "thermal_properties": thermal["thermal_properties"],
    }
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    if min(frequencies) < -0.001:
        raise SystemExit("声子路径出现负频率，请检查模型、受力和超胞收敛")
    print("已生成 band.yaml 与 thermal_properties.yaml，声子检查通过")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )


if __name__ == "__main__":
    main()
