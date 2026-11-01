"""使用 NEP 势优化结构，统一原子优化、晶胞优化与定体积模式。

用法：python calorine_relax.py POSCAR --model nep.txt --mode ions -o CONTCAR
--fmax 为收敛阈值/eV·Å⁻¹，--pressure 为外压/GPa；默认使用 Calorine CPUNEP。
"""

import argparse
from pathlib import Path


def relax(
    atoms, calculator, mode="ions", pressure=0.0, fmax=0.001, steps=1000, max_step=0.1
):
    from ase.filters import ExpCellFilter
    from ase.optimize import BFGS
    from ase.units import GPa

    atoms.calc = calculator
    target = atoms
    if mode != "ions":
        target = ExpCellFilter(
            atoms,
            scalar_pressure=pressure * GPa,
            constant_volume=mode == "constant-volume",
        )
    optimizer = BFGS(target, maxstep=max_step)
    converged = optimizer.run(fmax=fmax, steps=steps)
    return converged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", default=Path("POSCAR"))
    parser.add_argument("--model", type=Path, default=Path("nep.txt"))
    parser.add_argument(
        "--mode", choices=["ions", "cell", "constant-volume"], default="ions"
    )
    parser.add_argument("--backend", choices=["calorine", "pynep"], default="calorine")
    parser.add_argument(
        "--dispersion", action="store_true", help="叠加 PBE-D3(BJ)，需 dftd3"
    )
    parser.add_argument(
        "--pressure", type=float, default=0.0, help="外压/GPa，ions 模式不适用"
    )
    parser.add_argument("--fmax", type=float, default=0.001)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--max-step", type=float, default=0.1)
    parser.add_argument("-o", "--output", type=Path, default=Path("CONTCAR"))
    args = parser.parse_args()
    if not args.model.is_file() or args.output.exists():
        parser.error("模型不存在或输出结构已存在")
    if args.fmax <= 0 or args.steps <= 0 or args.max_step <= 0:
        parser.error("优化阈值、步数和步长必须为正")
    if args.mode == "ions" and args.pressure:
        parser.error("ions 模式不能指定外压")
    from ase.io import read, write

    if args.backend == "calorine":
        from calorine.calculators import CPUNEP

        calculator = CPUNEP(str(args.model.resolve()))
    else:
        from pynep.calculate import NEP

        calculator = NEP(str(args.model.resolve()))
    if args.dispersion:
        from ase.calculators.mixing import SumCalculator
        from dftd3.ase import DFTD3

        calculator = SumCalculator([calculator, DFTD3(method="pbe", damping="d3bj")])
    atoms = read(args.input)
    converged = relax(
        atoms,
        calculator,
        args.mode,
        args.pressure,
        args.fmax,
        args.steps,
        args.max_step,
    )
    write(args.output, atoms, format="vasp", direct=True)
    print(f"free energy TOTEN = {atoms.get_potential_energy():.10f} eV")
    print(f"优化收敛：{converged}")
    if not converged:
        parser.exit(1, "已保存最后结构，但未达到收敛阈值\n")


if __name__ == "__main__":
    main()
