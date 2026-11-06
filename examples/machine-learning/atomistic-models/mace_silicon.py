"""真实 MACE-MP small 硅静态检查；用法：python mace_silicon.py [--model 本地权重]。"""
import argparse
import os
import hashlib
import importlib.metadata
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from ase.build import bulk
with torch.serialization.safe_globals([slice]):
    from mace.calculators import mace_mp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="small", help="MACE-MP small 或本地对应权重路径")
    args = parser.parse_args()
    torch.set_num_threads(2)
    calc = mace_mp(model=args.model, device="cpu", default_dtype="float64", dispersion=False)
    lattice = np.linspace(5.25, 5.65, 9)
    energies = []
    for a in lattice:
        atoms = bulk("Si", "diamond", a=float(a))
        atoms.calc = calc
        energies.append(atoms.get_potential_energy()/len(atoms))
    primitive = bulk("Si", "diamond", a=5.43)
    primitive.calc = calc
    supercell = primitive.repeat((2, 2, 2))
    supercell.calc = calc
    replication_error = abs(supercell.get_potential_energy()/len(supercell)
                            - primitive.get_potential_energy()/len(primitive))
    distorted = primitive.copy()
    distorted.positions[0, 0] += 0.03
    distorted.calc = calc
    force = float(distorted.get_forces()[0, 0])
    step = 1e-4
    plus, minus = distorted.copy(), distorted.copy()
    plus.positions[0, 0] += step
    minus.positions[0, 0] -= step
    plus.calc = minus.calc = calc
    finite_difference = -(plus.get_potential_energy()-minus.get_potential_energy())/(2*step)
    assert replication_error < 1e-7
    assert abs(force-finite_difference) < 1e-5
    assert 0 < int(np.argmin(energies)) < len(lattice)-1
    Path("results").mkdir(exist_ok=True)
    np.savetxt("results/mace_si_scan.csv", np.column_stack([lattice, energies]),
               delimiter=",", header="lattice_A,energy_eV_per_atom", comments="")
    cache_files = [Path(args.model)] if Path(args.model).is_file() else list((Path(os.environ.get("XDG_CACHE_HOME", str(Path.home()/".cache")))/"mace").glob("*"))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in cache_files if p.is_file()}
    report = {"model": args.model, "mace_torch_version": importlib.metadata.version("mace-torch"),
              "torch_version": torch.__version__, "device": "cpu", "dtype": "float64", "dispersion": False,
              "sampled_minimum_lattice_A": float(lattice[np.argmin(energies)]),
              "replication_error_eV_per_atom": replication_error,
              "force_eV_per_A": force, "finite_difference_force_eV_per_A": float(finite_difference),
              "weight_sha256": hashes}
    Path("results/mace_si.json").write_text(json.dumps(report, indent=2))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(lattice, np.array(energies)-min(energies), "o-", color="#0072B2")
    ax.set(xlabel="Lattice parameter (angstrom)", ylabel="Relative energy (eV/atom)",
           title="Diamond Si, MACE-MP small, CPU float64")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig("results/mace_si_scan.png", dpi=180)
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
