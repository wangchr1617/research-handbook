"""重新加载 Cu/EMT 训练模型并核对验证数据；用法：python predict_trained.py。"""
import json
from pathlib import Path

import numpy as np
import torch
from ase.io import read
with torch.serialization.safe_globals([slice]):
    from mace.calculators import MACECalculator


def main():
    torch.set_num_threads(2)
    model = Path("results/models/Cu_EMT_fit.model")
    calculator = MACECalculator(model_paths=str(model), device="cpu", default_dtype="float64")
    energy_errors, force_errors = [], []
    for atoms in read("results/cu_valid.extxyz", index=":"):
        e_ref, f_ref = atoms.info["REF_energy"], atoms.arrays["REF_forces"].copy()
        atoms.calc = calculator
        energy_errors.append((atoms.get_potential_energy()-e_ref)/len(atoms))
        force_errors.extend((atoms.get_forces()-f_ref).ravel())
    e_rmse = float(np.sqrt(np.mean(np.square(energy_errors))))
    f_rmse = float(np.sqrt(np.mean(np.square(force_errors))))
    assert np.isfinite(e_rmse) and np.isfinite(f_rmse)
    report = {"reference": "ASE EMT, not DFT", "validation_structures": len(energy_errors),
              "energy_rmse_eV_per_atom": e_rmse, "force_component_rmse_eV_per_A": f_rmse,
              "checkpoint": str(model)}
    Path("results/cu_emt_validation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
