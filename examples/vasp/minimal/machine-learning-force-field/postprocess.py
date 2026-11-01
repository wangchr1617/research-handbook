"""用法：python3 postprocess.py；检查真实训练与纯预测状态，对独立构型比较 DFT 和 MLFF。"""

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from ase.io import read


def status_rows(directory):
    return [
        line.split()[1:]
        for line in (directory / "ML_LOGFILE").read_text().splitlines()
        if line.startswith("STATUS ")
    ]


def main():
    root = Path.cwd()
    for mode in ["train", "refit", "run", "reference"]:
        if "General timing and accounting" not in (root / mode / "OUTCAR").read_text(
            errors="replace"
        ):
            raise SystemExit(f"{mode} 未正常结束")
    training = status_rows(root / "train")
    prediction = status_rows(root / "run")
    input_text = Path("train/INCAR").read_text()
    expected_steps = int(re.search(r"(?m)^NSW\s*=\s*(\d+)", input_text).group(1))
    nelm = int(re.search(r"(?m)^NELM\s*=\s*(\d+)", input_text).group(1))
    if len(training) != expected_steps or not any(row[4] == "T" for row in training):
        raise SystemExit("没有确认训练出可用力场，或训练步数与本例不符")
    if not prediction or any(row[3] != "F" or row[4] != "T" for row in prediction):
        raise SystemExit("预测阶段没有确认纯力场计算")
    with Path("refit/ML_FFN").open("rb") as stream:
        header = stream.readline().decode("ascii", errors="replace")
    metadata = json.loads(header[header.index("{") : header.rindex("}") + 1])
    if not metadata.get("ML_LFAST") or metadata.get("training_structures", 0) < 1:
        raise SystemExit("重拟合模型头未确认快速模型或训练结构")
    train_xml = ET.parse("train/vasprun.xml")
    scf_steps = [
        len(step.findall("scstep")) for step in train_xml.findall("calculation")
    ]
    if not scf_steps or any(count >= nelm for count in scf_steps):
        raise SystemExit("训练参考计算存在电子未收敛步骤")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("check_vasp.py"))],
        cwd=root / "reference",
        check=True,
    )
    reference = read(root / "reference/vasprun.xml", format="vasp-xml")
    target = read(root / "run/POSCAR")
    # 独立构型不能与采样结构重复，距离按周期最小映像判断。
    differences = []
    for step in train_xml.findall("calculation"):
        position = step.find("structure/varray[@name='positions']")
        if position is not None:
            fractional = np.array(
                [list(map(float, row.text.split())) for row in position]
            )
            delta = (fractional - target.get_scaled_positions() + 0.5) % 1 - 0.5
            differences.append(float(np.linalg.norm(delta @ target.cell)))
    if not differences or min(differences) < 1e-4:
        raise SystemExit("测试构型与训练数据重复，不能作为独立对照")
    text = Path("run/OUTCAR").read_text(errors="replace")
    energies = re.findall(r"free\s+energy ML TOTEN\s*=\s*([-+0-9.Ee]+)", text)
    blocks = re.findall(
        r"POSITION\s+TOTAL-FORCE \(eV/Angst\) \(ML\)\s*\n\s*-+\s*\n(.*?)\n\s*-+",
        text,
        re.DOTALL,
    )
    if len(energies) != 1 or len(blocks) != 1:
        raise SystemExit("本例应有一次静态 ML 预测")
    rows = np.array([list(map(float, line.split())) for line in blocks[0].splitlines()])
    if rows.shape != (len(reference), 6) or not np.isfinite(rows).all():
        raise SystemExit("预测受力或坐标不完整")
    delta = (
        rows[:, :3] @ np.linalg.inv(target.cell) - target.get_scaled_positions() + 0.5
    ) % 1 - 0.5
    if np.linalg.norm(delta @ target.cell) > 1e-4 or not np.allclose(
        reference.cell, target.cell
    ):
        raise SystemExit("ML 预测坐标或晶胞与对照输入不一致")
    predicted_force = rows[:, 3:]
    reference_force = reference.get_forces()
    predicted_energy = float(energies[0])
    reference_energy = reference.get_potential_energy(force_consistent=True)
    result = {
        "training_steps": len(training),
        "training_dft_steps": sum(row[3] == "T" for row in training),
        "model_training_structures": metadata["training_structures"],
        "prediction_dft_steps": 0,
        "energy_error_meV_atom": (predicted_energy - reference_energy)
        / len(reference)
        * 1000,
        "force_RMSE_eV_A": float(
            np.sqrt(np.mean((predicted_force - reference_force) ** 2))
        ),
        "reference_forces_eV_A": reference_force.tolist(),
        "predicted_forces_eV_A": predicted_force.tolist(),
        "reference_energy_eV": reference_energy,
        "predicted_energy_eV": predicted_energy,
    }
    Path("mlff-results.json").write_text(json.dumps(result, indent=2) + "\n")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
