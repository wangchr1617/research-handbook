"""笔记引用脚本：真实转换与边界回归，运行 python -m pytest scripts/tests。"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from ase import Atoms
from ase.calculators.singlepoint import SinglePointCalculator
from ase.io import read, write

SCRIPTS = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(Path(name).stem, SCRIPTS / name)
    result = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str((SCRIPTS / name).parent))
    try:
        spec.loader.exec_module(result)
    finally:
        sys.path.pop(0)
    return result


def run(name, *args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *map(str, args)],
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=30,
    )


@pytest.fixture
def deepmd_data(tmp_path):
    root = tmp_path / "deepmd"
    root.mkdir()
    (root / "type.raw").write_text("0\n1\n")
    (root / "type_map.raw").write_text("H He\n")
    for index, frames in enumerate((2, 1)):
        folder = root / f"set.{index:03d}"
        folder.mkdir()
        offset = 0 if index == 0 else 2
        np.save(folder / "box.npy", np.tile(np.eye(3).reshape(1, 9) * 4, (frames, 1)))
        np.save(folder / "coord.npy", np.tile([0, 0, 0, 1, 1, 1], (frames, 1)))
        np.save(
            folder / "energy.npy",
            -np.arange(offset + 1, offset + frames + 1, dtype=float),
        )
        np.save(
            folder / "force.npy",
            np.arange(frames * 6, dtype=float).reshape(frames, 6) / 100,
        )
        np.save(
            folder / "virial.npy",
            np.tile(np.eye(3).reshape(1, 9) * (offset + 1), (frames, 1)),
        )
    return root


def test_all_deepmd_sets_and_absolute_paths_are_preserved(deepmd_data, tmp_path):
    output = tmp_path / "all.xyz"
    result = run("structure/deepmd_to_xyz.py", deepmd_data, "-o", output)
    assert result.returncode == 0, result.stderr
    actual = read(output, index=":")
    assert len(actual) == 3
    assert [a.get_potential_energy() for a in actual] == [-1, -2, -3]
    np.testing.assert_allclose(actual[2].info["virial"], np.eye(3) * 3)
    np.testing.assert_allclose(actual[2].get_forces(), np.arange(6).reshape(2, 3) / 100)
    assert actual[0].get_chemical_symbols() == ["H", "He"]
    initial = output.read_bytes()
    assert run("structure/deepmd_to_xyz.py", deepmd_data, "-o", output).returncode != 0
    assert output.read_bytes() == initial


def test_deepmd_database_all_sets_and_stress(deepmd_data, tmp_path):
    output = tmp_path / "all.db"
    result = run("structure/deepmd_to_ase.py", deepmd_data, "-o", output)
    assert result.returncode == 0, result.stderr
    actual = read(output, index=":")
    assert len(actual) == 3
    np.testing.assert_allclose(actual[-1].get_stress(voigt=False), -np.eye(3) * 3 / 64)


def test_deepmd_nopbc_and_missing_virial(deepmd_data, tmp_path):
    (deepmd_data / "nopbc").touch()
    for file in deepmd_data.glob("set.*/virial.npy"):
        file.unlink()
    output = tmp_path / "molecule.xyz"
    result = run("structure/deepmd_to_xyz.py", deepmd_data, "-o", output)
    assert result.returncode == 0, result.stderr
    actual = read(output, index=":")
    assert not actual[0].pbc.any()
    assert "virial" not in actual[0].info


@pytest.mark.parametrize(
    "fault", ["missing_map", "missing_force", "nonfinite", "bad_shape"]
)
def test_invalid_deepmd_never_publishes_output(deepmd_data, tmp_path, fault):
    if fault == "missing_map":
        (deepmd_data / "type_map.raw").unlink()
    elif fault == "missing_force":
        (deepmd_data / "set.001/force.npy").unlink()
    elif fault == "nonfinite":
        np.save(deepmd_data / "set.001/energy.npy", [np.nan])
    else:
        np.save(deepmd_data / "set.001/force.npy", np.zeros((1, 9)))
    for script, suffix in [("deepmd_to_xyz.py", ".xyz"), ("deepmd_to_ase.py", ".db")]:
        output = tmp_path / (script + suffix)
        result = run("structure/" + script, deepmd_data, "-o", output)
        assert result.returncode != 0, result.stdout
        assert not output.exists()


@pytest.mark.parametrize("version", [1, 2, 3])
def test_legacy_nep_output_keeps_frame_count(deepmd_data, tmp_path, version):
    output = tmp_path / "train.in"
    result = run(
        "structure/deepmd_to_xyz.py",
        deepmd_data,
        "-o",
        output,
        "--format",
        "nep",
        "--nep-version",
        version,
    )
    assert result.returncode == 0, result.stderr
    lines = output.read_text().splitlines()
    assert lines[:4] == ["3", "2 1", "2 1", "2 1"]
    assert len(lines) == 4 + 3 * 4


def test_extxyz_deepmd_roundtrip_and_no_clobber(tmp_path):
    source = tmp_path / "train.xyz"
    atoms = Atoms("HHe", positions=[[0, 0, 0], [1, 1, 1]], cell=[4, 4, 4], pbc=True)
    atoms.calc = SinglePointCalculator(
        atoms, energy=-5, forces=np.ones((2, 3)), stress=np.eye(3) * 0.1
    )
    write(source, [atoms, atoms, atoms])
    output = tmp_path / "train"
    result = run("structure/xyz_to_deepmd.py", source, "-o", output, "--set-size", 2)
    assert result.returncode == 0, result.stderr
    restored = tmp_path / "restored.xyz"
    result = run("structure/deepmd_to_xyz.py", output, "-o", restored)
    assert result.returncode == 0, result.stderr
    frames = read(restored, index=":")
    assert len(frames) == 3
    assert frames[0].get_potential_energy() == -5
    np.testing.assert_allclose(frames[0].get_forces(), np.ones((2, 3)))
    assert run("structure/xyz_to_deepmd.py", source, "-o", output).returncode != 0


def test_capacity_stoichiometry_and_same_formula_rows(tmp_path):
    source = tmp_path / "structures"
    source.mkdir()
    atoms = Atoms("C6", cell=[10, 10, 10], pbc=True)
    for name in ["one.vasp", "two.vasp"]:
        write(source / name, atoms, format="vasp")
    m = module("analysis/calculate_capacity.py")
    rows = m.calculate_capacity(
        source, ["Li", "Mg"], 1, output=tmp_path / "capacity.csv"
    )
    assert len(rows) == 2
    expected = 96485.33212 / (3.6 * atoms.get_masses().sum())
    assert rows[0]["Li"] == pytest.approx(expected)
    assert rows[0]["Mg"] == pytest.approx(expected * 2)
    assert rows[0]["source"] != rows[1]["source"]
    result = run(
        "analysis/calculate_capacity.py", source, "Li", 1, "-o", tmp_path / "cli.csv"
    )
    assert result.returncode == 0, result.stderr
    with pytest.raises(ValueError):
        m.calculate_capacity(source, ["Li"], np.nan, output=tmp_path / "invalid.csv")


def test_descriptor_units_shape_and_aggregation(tmp_path):
    m = module("deepmd/extract_deepmd_descriptors.py")
    atoms = Atoms("HHe", cell=[4, 4, 4], pbc=True)
    atoms.calc = SinglePointCalculator(atoms, energy=-8)

    class Model:
        def eval_descriptor(self, coords, cell, types):
            return np.array([[[1, 2, 3], [3, 4, 5]]], dtype=float)

        def eval(self, coords, cell, types, atomic=False):
            return [None, None, None, np.array([[[-2], [-6]]])]

    descriptors, energies = m.extract(Model(), [atoms], ["H", "He"], atomic=True)
    np.testing.assert_allclose(descriptors, [[1, 2, 3], [3, 4, 5]])
    np.testing.assert_allclose(energies, [-2, -6])
    descriptors, energies = m.extract(Model(), [atoms], ["H", "He"], aggregation="mean")
    np.testing.assert_allclose(descriptors, [[2, 3, 4]])
    np.testing.assert_allclose(energies, [-4])
    with pytest.raises(ValueError):
        m.extract(Model(), [atoms], ["H"])


def test_chemiscope_pca_constant_and_small_datasets():
    m = module("visualization/create_chemiscope_input.py")
    projection = m.project([[1, 1], [2, 1]], [-1, -2], 2)
    assert projection.shape == (2, 3)
    assert np.isfinite(projection).all()
    np.testing.assert_allclose(m.project([[1, 1]], [-1], 1), 0)
    for descriptors, energy, count in [
        ([[1, 2]], [-1], 2),
        ([[np.nan]], [-1], 1),
        ([[1]], [[-1]], 1),
    ]:
        with pytest.raises(ValueError):
            m.project(descriptors, energy, count)


def test_rdf_excludes_self_without_erasing_first_bin():
    m = module("analysis/calculate_rdf.py")

    class Group:
        indices = np.array([0, 1])

        def __len__(self):
            return 2

    class Universe:
        def select_atoms(self, selection, updating=False):
            return Group()

    options = {}

    class RDF:
        def __init__(self, a, b, **kwargs):
            options.update(kwargs)
            self.results = SimpleNamespace(bins=[0.1, 0.2], rdf=[2, 3])

        def run(self, **kwargs):
            options.update(kwargs)

    actual = m.calculate(Universe(), rmax=1, rdf_factory=RDF)
    assert options["exclusion_block"] == (1, 1)
    assert actual[0, 1] == 2
    with pytest.raises(ValueError):
        m.calculate(Universe(), updating=True)
    with pytest.raises(ValueError):
        m.calculate(Universe(), rmax=np.nan)


def test_collector_rejects_nonfinite_and_fractional_steps(tmp_path):
    m = module("deepmd/collect_dpgen_deviations.py")
    path = tmp_path / "model_devi.out"
    for row in ["0.5 nan", "0 nan", "0 -1", "nan 1", "0 inf"]:
        path.write_text("# step max_devi_f\n" + row + "\n")
        with pytest.raises(ValueError):
            m.collect(tmp_path)


def test_preparation_rejects_formatted_name_collision_before_writing(tmp_path):
    m = module("vasp/prepare_jobs.py")
    target = tmp_path / "tasks"
    with pytest.raises(FileExistsError):
        m.prepare_parameter(tmp_path, target, [300, 300.00001], "encut")
    assert not target.exists()
    with pytest.raises(ValueError):
        m.prepare_parameter(tmp_path, target, [np.nan], "encut")


def test_vasp_summary_recursive_does_not_duplicate_root(tmp_path):
    (tmp_path / "OUTCAR").write_text("NIONS = 1\n")
    output = tmp_path / "results.csv"
    result = run("vasp/summarize_outputs.py", tmp_path, "--recursive", "-o", output)
    assert result.returncode == 0, result.stderr
    assert len(output.read_text().splitlines()) == 2
    assert run("vasp/summarize_outputs.py", tmp_path, "-o", output).returncode != 0


@pytest.mark.parametrize(
    "name",
    [
        "structure/deepmd_to_xyz.py",
        "structure/xyz_to_deepmd.py",
        "analysis/calculate_capacity.py",
        "analysis/calculate_rdf.py",
        "deepmd/extract_deepmd_descriptors.py",
        "visualization/create_chemiscope_input.py",
    ],
)
def test_help_does_not_load_optional_heavy_dependencies(name):
    result = run(name, "--help")
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_phase_statistics_reject_invalid_sampling():
    m = module("materials/analyze_phase.py")
    atoms = Atoms(
        "GeGeTeTe",
        positions=[[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]],
        cell=[10, 10, 10],
        pbc=True,
    )
    with pytest.raises(ValueError):
        m.safe_radius(np.zeros((3, 3)))
    for edges in [[0, 1, 1], [0, np.nan, 2], [-1, 0, 1]]:
        with pytest.raises(ValueError):
            m.partial_rdf([atoms], edges)
    with pytest.raises(ValueError):
        m.partial_rdf([], [0, 1])
    with pytest.raises(ValueError):
        m.coordination([atoms], np.nan)
    atoms.pbc = False
    with pytest.raises(ValueError):
        m.drift_corrected_msd([atoms])


def test_materials_plot_rejects_broken_symlink(tmp_path):
    target = tmp_path / "broken.png"
    target.symlink_to(tmp_path / "missing.png")
    result = run("materials/plot_results.py", "inorganic", tmp_path, "--output", target)
    assert result.returncode != 0
    assert target.is_symlink()
    assert not (tmp_path / "missing.png").exists()
