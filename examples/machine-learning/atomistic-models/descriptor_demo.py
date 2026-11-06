"""比较真实 ACSF/SOAP 实现与最低阶矩张量；用法：python descriptor_demo.py。"""
import json
from pathlib import Path

import numpy as np
from ase import Atoms
from dscribe.descriptors import ACSF, SOAP


def environment(angle_deg):
    """中心 O 与两条 1 Å 的 O-H 键；只改变键角。"""
    angle = np.deg2rad(angle_deg)
    return Atoms("OHH", positions=[[0, 0, 0], [1, 0, 0],
                                   [np.cos(angle), np.sin(angle), 0]])


def moment_features(atoms):
    r = atoms.positions[1:] - atoms.positions[0]
    weights = np.exp(-np.linalg.norm(r, axis=1))
    m0 = weights.sum()
    m1 = (weights[:, None] * r).sum(axis=0)
    return np.array([m0, m1 @ m1])


def main():
    acsf = ACSF(species=["H", "O"], r_cut=4.0,
                g2_params=[[1.0, 0.0]], g4_params=[[1.0, 1.0, 1.0]])
    soap = SOAP(species=["H", "O"], periodic=False, r_cut=4.0,
                n_max=3, l_max=2, sigma=0.3, sparse=False)
    a, b = environment(90), environment(120)
    rotated = a.copy()
    rotated.rotate(37, "z", rotate_cell=False)
    permuted = a[[0, 2, 1]]
    report = {}
    for name, descriptor in [("ACSF", acsf), ("SOAP", soap)]:
        x = descriptor.create(a, centers=[0])[0]
        y = descriptor.create(b, centers=[0])[0]
        xr = descriptor.create(rotated, centers=[0])[0]
        xp = descriptor.create(permuted, centers=[0])[0]
        rotation_error = float(np.max(np.abs(x - xr)))
        permutation_error = float(np.max(np.abs(x - xp)))
        assert rotation_error < 1e-9 and permutation_error < 1e-9
        assert np.linalg.norm(x - y) > 1e-6
        report[name] = {"dimension": len(x), "angle_change_norm": float(np.linalg.norm(x-y)),
                        "rotation_error": rotation_error, "permutation_error": permutation_error}
    ma, mb = moment_features(a), moment_features(b)
    assert np.isclose(ma[0], mb[0]) and not np.isclose(ma[1], mb[1])
    assert np.allclose(ma, moment_features(rotated))
    report["moment_features"] = {"90_deg": ma.tolist(), "120_deg": mb.tolist()}
    Path("results").mkdir(exist_ok=True)
    Path("results/descriptors.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
