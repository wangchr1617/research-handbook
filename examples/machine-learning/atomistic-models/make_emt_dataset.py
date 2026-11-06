"""生成可训练的 Cu/EMT 小数据；用法：python make_emt_dataset.py；标签不是 DFT。"""
from pathlib import Path

import numpy as np
from ase.build import bulk
from ase.calculators.emt import EMT
from ase.io import write


def main():
    rng = np.random.default_rng(21)
    train, valid = [], []
    for i in range(24):
        atoms = bulk("Cu", "fcc", a=float(rng.uniform(3.50, 3.75)), cubic=True)
        atoms.positions += rng.normal(scale=0.035, size=atoms.positions.shape)
        atoms.calc = EMT()
        # 使用独立的 REF_* 字段，避免新 ASE 版本对保留字段的处理差异。
        atoms.info["REF_energy"] = float(atoms.get_potential_energy())
        atoms.arrays["REF_forces"] = atoms.get_forces().copy()
        atoms.calc = None
        (valid if i % 6 == 0 else train).append(atoms)
    Path("results").mkdir(exist_ok=True)
    write("results/cu_train.extxyz", train, format="extxyz")
    write("results/cu_valid.extxyz", valid, format="extxyz")
    print(f"train={len(train)}, valid={len(valid)}; reference=ASE EMT, not DFT")


if __name__ == "__main__":
    main()
