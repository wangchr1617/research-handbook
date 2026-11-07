"""氧化态模型回归；需要 pymatgen，可在已有科研环境单独运行本文件。"""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("pymatgen.core")
from pymatgen.core import Element, Lattice, Structure

spec = importlib.util.spec_from_file_location(
    "battery_capacity",
    Path(__file__).resolve().parents[1] / "analysis/battery_capacity.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def structure(lithium=True):
    symbols = (
        ["Li", "Fe", "P", "O", "O", "O", "O"]
        if lithium
        else ["Fe", "P", "O", "O", "O", "O"]
    )
    atoms = Structure(
        Lattice.cubic(10),
        symbols,
        [[i / len(symbols), 0, 0] for i in range(len(symbols))],
    )
    atoms.add_oxidation_state_by_element(
        {"Li": 1, "Fe": 2 if lithium else 3, "P": 5, "O": -2}
    )
    return atoms


def test_element_cation_and_capacity_units():
    atoms = structure()
    analyzer = module.BatteryAnalyzer(atoms, Element("Li"))
    assert analyzer.max_cation_removal == 1
    expected = 96485.33212 / (3.6 * atoms.composition.weight)
    assert analyzer.get_max_capgrav(1) == pytest.approx(expected, rel=1e-8)
    expected_volume = 1.602176634e-19 / 3.6 / (atoms.volume * 1e-24)
    assert analyzer.get_max_capvol() == pytest.approx(expected_volume, rel=1e-8)


def test_insertion_and_invalid_values():
    analyzer = module.BatteryAnalyzer(structure(False))
    assert analyzer.max_cation_insertion == 1
    for charge in [0, -1, np.nan, np.inf]:
        with pytest.raises(ValueError):
            module.BatteryAnalyzer(structure(), cation_charge=charge)
    for count in [-1, np.nan]:
        with pytest.raises(ValueError):
            analyzer.get_max_capgrav(count)
    with pytest.raises(ValueError):
        analyzer.get_max_capvol(volume=0)


def test_neutrality_and_missing_oxidation_states():
    atoms = structure()
    atoms.add_oxidation_state_by_element({"Li": 1, "Fe": 3, "P": 5, "O": -2})
    with pytest.raises(ValueError, match="电中性"):
        module.BatteryAnalyzer(atoms)
    atoms.remove_oxidation_states()
    with pytest.raises(ValueError, match="氧化态"):
        module.BatteryAnalyzer(atoms)
