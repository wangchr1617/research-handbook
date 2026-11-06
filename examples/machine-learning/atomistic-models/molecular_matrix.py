"""真实水分子 RHF/STO-3G 矩阵、轨道与电荷核对；用法：python molecular_matrix.py。"""
import json
from pathlib import Path

import numpy as np
from pyscf import gto, scf
from scipy.linalg import eigh


def main():
    mol = gto.M(atom="O 0 0 0; H 0 -0.757 0.587; H 0 0.757 0.587",
                basis="sto-3g", unit="Angstrom", charge=0, spin=0, verbose=0)
    mf = scf.RHF(mol)
    mf.conv_tol = 1e-11
    total_energy = mf.kernel()
    assert mf.converged
    overlap = mf.get_ovlp()
    fock = mf.get_fock()
    density = mf.make_rdm1()
    energies, orbitals = eigh(fock, overlap)
    residual = np.linalg.norm(fock @ orbitals - (overlap @ orbitals) * energies)
    electrons = float(np.trace(density @ overlap))
    assert residual < 1e-9 and abs(electrons - mol.nelectron) < 1e-8
    assert np.allclose(energies, mf.mo_energy, atol=1e-7)
    # 同时变换两个矩阵，验证换基不改变能谱。
    gauge = np.diag([1., 1., -1., 1., 1., 1., 1.])
    assert np.allclose(eigh(gauge.T @ fock @ gauge, gauge.T @ overlap @ gauge)[0], energies)
    Path("results").mkdir(exist_ok=True)
    np.savez("results/water_rhf.npz", hamiltonian=fock, overlap=overlap,
             density=density, eigenvalues=energies, coefficients=orbitals)
    report = {"method": "RHF/STO-3G", "basis_dimension": mol.nao_nr(),
              "electrons": electrons, "total_energy_Ha": total_energy,
              "orbital_energies_Ha": energies.tolist(),
              "occupied_eigenvalue_sum_Ha": float(2 * energies[:mol.nelectron//2].sum()),
              "generalized_eigen_residual": float(residual), "ao_labels": mol.ao_labels()}
    Path("results/water_rhf.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
