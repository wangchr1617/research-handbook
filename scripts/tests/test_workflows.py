"""核心转换与批处理的回归测试。运行：python -m pytest scripts/tests -q。"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from ase import Atoms
from ase.calculators.singlepoint import SinglePointCalculator
from ase.io import read, write

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS / "cp2k"))


def module(relative):
    path = SCRIPTS / relative
    spec = importlib.util.spec_from_file_location(path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def run(relative, *arguments, cwd=None, check=True):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / relative), *map(str, arguments)],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=check,
    )


@pytest.fixture
def atoms():
    image = Atoms("GeTe", positions=[[0, 0, 0], [1, 1, 1]], cell=[4, 4, 4], pbc=True)
    image.calc = SinglePointCalculator(
        image,
        energy=-3.0,
        free_energy=-3.2,
        forces=[[1, 2, 3], [4, 5, 6]],
        stress=[1, 2, 3, 0.4, 0.5, 0.6],
    )
    return image


def test_summary_units_and_completion(tmp_path):
    (tmp_path / "OUTCAR").write_text(""" NIONS = 2
 free energy TOTEN = -5 eV
 energy without entropy = -4.2 energy(sigma->0) = -4.1
 volume of cell : 64.0
 entropy T*S EENTRO = 0.1
 Found 12 irreducible k-points:
 General timing and accounting informations
 reached required accuracy
""")
    (tmp_path / "OSZICAR").write_text("DAV: 2 x\n 1 F= -5 E0= -4.1\n")
    result = module("vasp/summarize_outputs.py").summarize(tmp_path)
    assert result["energy_eV"] == -4.1
    assert result["energy_per_atom_eV"] == -2.05
    assert result["volume_A3"] == 64
    assert result["entropy_eV"] == 0.1
    assert result["irreducible_kpoints"] == 12
    assert result["finished"] and result["ionic_converged"]
    (tmp_path / "OUTCAR").write_text("NIONS = 2\n")
    result = module("vasp/summarize_outputs.py").summarize(tmp_path)
    assert not result["finished"] and result["energy_eV"] is None


def test_prepare_jobs_encut_and_no_clobber(tmp_path, atoms):
    source = tmp_path / "input"
    source.mkdir()
    (source / "INCAR").write_text("ENCUT = 250; ISMEAR = 0\nENCUT=200\n")
    (source / "POTCAR").write_text("fixture")
    write(source / "POSCAR", atoms, format="vasp")
    output = tmp_path / "tasks"
    run(
        "vasp/prepare_jobs.py",
        "encut",
        300,
        400,
        "--source",
        source,
        "--output",
        output,
    )
    assert (output / "300/INCAR").read_text().count("ENCUT") == 1
    assert "ISMEAR = 0" in (output / "300/INCAR").read_text()
    assert "ENCUT=200" in (source / "INCAR").read_text()
    failed = run(
        "vasp/prepare_jobs.py",
        "encut",
        300,
        "--source",
        source,
        "--output",
        output,
        check=False,
    )
    assert failed.returncode != 0
    run(
        "vasp/prepare_jobs.py",
        "scale",
        1.1,
        "--source",
        source,
        "--output",
        tmp_path / "scaled",
    )
    image = read(tmp_path / "scaled/1.1/POSCAR")
    assert image.get_volume() == pytest.approx(atoms.get_volume() * 1.1**3)


def test_collect_and_prepare_structures(tmp_path, atoms):
    source = tmp_path / "calculations"
    (source / "a").mkdir(parents=True)
    write(source / "a/CONTCAR", atoms, format="vasp")
    output = tmp_path / "collected"
    run("vasp/collect_structures.py", source, "--output", output)
    assert (output / "a.vasp").is_file()
    run(
        "vasp/prepare_jobs.py",
        "structures",
        str(output / "*.vasp"),
        "--output",
        tmp_path / "jobs",
    )
    assert (tmp_path / "jobs/a/POSCAR").is_file()


def test_training_frame_virial_and_energy_roundtrip(tmp_path, atoms):
    m = module("structure/vasp_to_xyz.py")
    result = m.training_frame(atoms, "test", "free", True, energy_shift=0.5)
    assert result.get_potential_energy() == pytest.approx(-4.2)
    expected = -atoms.get_stress(voigt=False) * atoms.get_volume()
    np.testing.assert_allclose(result.info["virial"], expected)
    np.testing.assert_allclose(result.get_forces(), atoms.get_forces())
    path = tmp_path / "train.xyz"
    write(path, result, format="extxyz")
    restored = read(path)
    np.testing.assert_allclose(restored.info["virial"], expected)
    assert restored.get_potential_energy() == pytest.approx(-4.2)
    assert m.training_frame(atoms, "zero", "zero", False).get_potential_energy() == -3
    assert "stress" in atoms.calc.results  # 输入 calculator 不能被转换器破坏。


def test_convergence_alignment(tmp_path):
    m = module("structure/vasp_to_xyz.py")
    (tmp_path / "OUTCAR").write_text(" NELM = 60\n")
    (tmp_path / "OSZICAR").write_text(
        "DAV: 3 0\n 1 F= 0 E0= 0\nRMM: 60 0\n 2 F= 0 E0= 0\n"
    )
    assert m.convergence_mask(tmp_path, 2) == [True, False]
    with pytest.raises(ValueError, match="数量不一致"):
        m.convergence_mask(tmp_path, 1)


def test_vasp_outcar_real_fixture(tmp_path):
    import ase

    fixture = Path(ase.__file__).parent / "test/testdata/vasp/OUTCAR_example_1"
    if not fixture.exists():
        pytest.skip("此 ASE 安装未附带官方 OUTCAR 测试样本")
    directory = tmp_path / "calculation"
    directory.mkdir()
    (directory / "OUTCAR").write_bytes(fixture.read_bytes())
    m = module("structure/vasp_to_xyz.py")
    output = tmp_path / "train.xyz"
    assert m.convert(tmp_path, output, frames="all") > 0
    reference = read(directory / "OUTCAR", index=":", format="vasp-out")
    actual = read(output, index=":")
    assert len(reference) == len(actual)
    for a, b in zip(reference, actual):
        assert a.get_potential_energy(force_consistent=True) == pytest.approx(
            b.get_potential_energy()
        )
        np.testing.assert_allclose(a.get_forces(), b.get_forces(), atol=1e-7)


def test_training_output_is_atomic_on_failure(tmp_path):
    (tmp_path / "OUTCAR").write_text("invalid OUTCAR")
    output = tmp_path / "train.xyz"
    with pytest.raises(Exception):
        module("structure/vasp_to_xyz.py").convert(tmp_path, output)
    assert not output.exists()
    assert not list(tmp_path.glob("tmp*.xyz"))


def test_convert_structure_cell_and_repeat(tmp_path, atoms):
    write(tmp_path / "POSCAR", atoms, format="vasp")
    write(tmp_path / "plain.xyz", atoms, format="xyz")
    run(
        "structure/convert_structure.py",
        tmp_path / "plain.xyz",
        tmp_path / "last.cif",
        "--cell-from",
        tmp_path / "POSCAR",
    )
    assert read(tmp_path / "last.cif").get_volume() == pytest.approx(atoms.get_volume())
    run(
        "structure/convert_structure.py",
        tmp_path / "POSCAR",
        tmp_path / "super.xyz",
        "--repeat",
        2,
        1,
        1,
    )
    assert len(read(tmp_path / "super.xyz")) == 4


def test_unwrap_preserves_first_frame(tmp_path):
    images = [
        Atoms("H", scaled_positions=[[x, 0, 0]], cell=[10, 10, 10], pbc=True)
        for x in (0.9, 0.1, 0.4, 0.8, 0.2)
    ]
    source, output = tmp_path / "wrapped.xyz", tmp_path / "unwrapped.xyz"
    write(source, images)
    run("structure/convert_structure.py", source, output, "--unwrap")
    actual = read(output, index=":")
    np.testing.assert_allclose([a.positions[0, 0] for a in actual], [9, 11, 14, 18, 22])


def test_grouping_keeps_properties(tmp_path, atoms):
    source, output = tmp_path / "model.xyz", tmp_path / "grouped.xyz"
    write(source, [atoms, atoms])
    run("structure/group_xyz.py", source, output, "--species", "Ge=0", "Te=1")
    images = read(output, index=":")
    assert len(images) == 2
    np.testing.assert_array_equal(images[0].arrays["group"], [0, 1])
    np.testing.assert_allclose(images[0].get_forces(), atoms.get_forces())
    m = module("structure/group_xyz.py")
    with pytest.raises(ValueError, match="未分组"):
        m.assign_groups(atoms.copy(), ranges="0:0.5:0")


CP2K = """&GLOBAL
 RUN_TYPE MD
&END GLOBAL
&FORCE_EVAL
 &SUBSYS
  &CELL
   ABC 4 4 4
  &END CELL
  &COORD
   Ge 0 0 0
  &END COORD
 &END SUBSYS
&END FORCE_EVAL
&MOTION
 &MD
  STEPS 2
 &END MD
 &PRINT
  &CELL
  &END CELL
 &END PRINT
&END MOTION
"""


def test_cp2k_nested_blocks_and_velocity(tmp_path):
    m = module("cp2k/apply_cp2k_restart.py")
    restart = CP2K.replace("ABC 4 4 4", "ABC 5 5 5").replace("STEPS 2", "STEPS 9")
    restart = restart.replace(
        " &END SUBSYS", " &VELOCITY\n Ge 1 2 3\n &END VELOCITY\n &END SUBSYS"
    )
    result = m.apply_restart(restart, CP2K)
    assert "ABC 5 5 5" in result and "STEPS 9" in result
    assert "Ge 1 2 3" in result
    assert result.count("&CELL") == 2
    source, target = tmp_path / "restart.inp", tmp_path / "input.inp"
    source.write_text(restart)
    target.write_text(CP2K)
    target.chmod(0o640)
    run("cp2k/apply_cp2k_restart.py", source, target, "--in-place")
    assert target.with_name("input.inp.bak").read_text() == CP2K
    assert "ABC 5 5 5" in target.read_text()
    assert target.stat().st_mode & 0o777 == 0o640


def test_cp2k_rejects_ambiguous_force_eval():
    m = module("cp2k/apply_cp2k_restart.py")
    with pytest.raises(ValueError):
        m.apply_restart(CP2K + CP2K, CP2K)


def test_gpumd_count_and_truncated_frame(tmp_path):
    m = module("gpumd/check_gpumd.py")
    path = tmp_path / "dump.xyz"
    path.write_text("1\ncomment\nH 0 0 0\n1\ncomment\nH 1 1 1\n")
    assert m.frame_count(path) == 2
    path.write_text("2\ncomment\nH 0 0 0\n")
    with pytest.raises(ValueError):
        m.frame_count(path)


def test_deviation_reads_header_not_temperature_duplicates(tmp_path):
    m = module("deepmd/collect_dpgen_deviations.py")
    path = tmp_path / "model_devi.out"
    path.write_text(
        "# step max_devi_e min_devi_e avg_devi_e max_devi_f\n0 1 2 3 0.5\n10 1 2 3 0.8\n"
    )
    rows = m.collect(tmp_path)
    assert [row["max_devi_f"] for row in rows] == [0.5, 0.8]
    assert len(rows) == 2
    path.write_text("0 1 2 3 0.5\n")
    with pytest.raises(ValueError):
        m.collect(tmp_path)
    assert m.collect(tmp_path, 4)[0]["max_devi_f"] == 0.5


def test_random_displacement_seed_and_elements(tmp_path, atoms):
    source = tmp_path / "POSCAR"
    write(source, atoms, format="vasp")
    for name in ("one", "two"):
        run(
            "structure/random_displacement.py",
            source,
            "--elements",
            "Ge",
            "--count",
            2,
            "--seed",
            42,
            "--output-dir",
            tmp_path / name,
        )
    a = read(tmp_path / "one/displaced_0000.vasp")
    b = read(tmp_path / "two/displaced_0000.vasp")
    np.testing.assert_allclose(a.positions, b.positions)
    np.testing.assert_allclose(a.positions[1], atoms.positions[1])
    assert not np.allclose(a.positions[0], atoms.positions[0])


def test_segmented_interpolation_endpoints(atoms):
    m = module("structure/generate_dimer_scan.py")
    final = atoms.copy()
    final.positions[1] += [1, 0, 0]
    result = m.interpolate(atoms, final, 3)
    assert len(result) == 5
    np.testing.assert_allclose(result[0].positions, atoms.positions)
    np.testing.assert_allclose(result[-1].positions, final.positions)


def test_msd_plot_multiple_formats(tmp_path):
    first, second = tmp_path / "msd.out", tmp_path / "MSD.dat"
    first.write_text("0 0 0 0\n1 1 2 3\n")
    second.write_text("t x y z total sqrt\n0 0 0 0 0 0\n1 1 2 3 6 2\n")
    run("plotting/plot_msd.py", first, "-o", tmp_path / "components.png")
    run(
        "plotting/plot_msd.py",
        second,
        second,
        "--skiprows",
        1,
        "--columns",
        4,
        "--time-unit",
        "fs",
        "-o",
        tmp_path / "total.png",
    )
    assert (tmp_path / "components.png").stat().st_size > 100
    assert (tmp_path / "total.png").stat().st_size > 100


def test_relax_ions_with_ase_calculator(tmp_path, monkeypatch):
    from ase.calculators.emt import EMT

    monkeypatch.chdir(tmp_path)
    image = Atoms("Cu2", positions=[[0, 0, 0], [2.6, 0, 0]], cell=[10, 10, 10])
    result = module("gpumd/calorine/calorine_relax.py").relax(
        image, EMT(), fmax=0.05, steps=100
    )
    assert result
    assert np.max(np.linalg.norm(image.get_forces(), axis=1)) < 0.05


@pytest.mark.parametrize(
    "script",
    [
        "vasp/summarize_outputs.py",
        "vasp/prepare_jobs.py",
        "vasp/collect_structures.py",
        "vasp/run_elastic.py",
        "structure/convert_structure.py",
        "structure/vasp_to_xyz.py",
        "structure/slice_xdatcar.py",
        "structure/group_xyz.py",
        "structure/mcsqs_convert.py",
        "structure/generate_dimer_scan.py",
        "structure/random_displacement.py",
        "structure/convert_cp2k_structure.py",
        "cp2k/apply_cp2k_restart.py",
        "cp2k/convert_cp2k_run_type.py",
        "gpumd/check_gpumd.py",
        "deepmd/collect_dpgen_deviations.py",
        "plotting/plot_msd.py",
        "gpumd/calorine/calorine_relax.py",
    ],
)
def test_help_does_not_require_optional_scientific_programs(script):
    result = run(script, "--help")
    assert result.returncode == 0 and "usage:" in result.stdout


def executable(tmp_path, name, body):
    path = tmp_path / name
    path.write_text(f"#!{sys.executable}\n" + body)
    path.chmod(0o755)
    return path


def test_mcsqs_external_contract(tmp_path):
    source = tmp_path / "bestsqs.out"
    source.write_text("original SQS")
    fake = executable(
        tmp_path,
        "sqs2poscar",
        "import pathlib,sys\np=pathlib.Path(sys.argv[1])\np.with_name(p.name+'-POSCAR').write_text('comment\\nxxx\\n1 0 0\\n0 1 0\\n0 0 1\\nH\\n1\\nDirect\\n0 0 0\\n')\n",
    )
    output = tmp_path / "converted"
    run(
        "structure/mcsqs_convert.py",
        str(source),
        "--format",
        "vasp",
        "--output-dir",
        output,
        "--executable",
        fake,
    )
    assert read(output / "bestsqs.vasp").get_volume() == pytest.approx(1)
    assert source.read_text() == "original SQS"
    assert not source.with_name("bestsqs.out-POSCAR").exists()


def test_multiwfn_scf_external_contract(tmp_path):
    source = tmp_path / "input.inp"
    source.write_text("""&GLOBAL
 RUN_TYPE ENERGY
&END GLOBAL
&FORCE_EVAL
 &DFT
  &SCF
   EPS_SCF 1e-5
  &END SCF
 &END DFT
&END FORCE_EVAL
""")
    generated = source.read_text().replace("1e-5", "1e-6")
    fake = executable(
        tmp_path,
        "Multiwfn",
        "import pathlib,sys\ncommands=sys.stdin.read()\nassert 'cp2k\\ntemp.inp\\n4' in commands\npathlib.Path('temp.inp').write_text("
        + repr(generated)
        + ")\n",
    )
    output = tmp_path / "ot.inp"
    run(
        "cp2k/convert_cp2k_run_type.py",
        source,
        "ot",
        "-o",
        output,
        "--executable",
        fake,
    )
    assert "1e-6" in output.read_text()
    assert "1e-5" in source.read_text()


def test_multiwfn_geometry_external_contract(tmp_path):
    source = tmp_path / "restart.inp"
    source.write_text(CP2K)
    fake = executable(
        tmp_path,
        "Multiwfn",
        "import pathlib,sys\nassert '\\n100\\n2\\n33\\n' in sys.stdin.read()\npathlib.Path('converted.cif').write_text('mock-cif')\n",
    )
    output = tmp_path / "converted"
    run(
        "structure/convert_cp2k_structure.py",
        source,
        "--format",
        "cif",
        "--output-dir",
        output,
        "--executable",
        fake,
    )
    assert (output / "converted.cif").read_text() == "mock-cif"


def test_kpoints_external_contract(tmp_path):
    (tmp_path / "jobs/a").mkdir(parents=True)
    (tmp_path / "jobs/a/INCAR").write_text("ENCUT=300\n")
    fake = executable(
        tmp_path,
        "vaspkit",
        "import pathlib,sys\nassert sys.stdin.read()=='102\\n2\\n0.04\\n'\npathlib.Path('KPOINTS').write_text('mock-kpoints')\n",
    )
    run("vasp/prepare_jobs.py", "kpoints", tmp_path / "jobs", "--executable", fake)
    assert (tmp_path / "jobs/a/KPOINTS").is_file()


def test_cp2k_keyword_scope_and_anonymous_end():
    m = module("cp2k/cp2k_sections.py")
    text = "&GLOBAL ! comment\n run_type MD\n&end\n&FORCE_EVAL\n &DFT\n  &SCF\n EPS_SCF 1e-6\n &end\n &end\n&end\n"
    assert m.keyword(text, ("GLOBAL",), "RUN_TYPE") == "MD"
    changed = m.set_keyword(text, ("GLOBAL",), "RUN_TYPE", "CELL_OPT")
    assert m.keyword(changed, ("GLOBAL",), "RUN_TYPE") == "CELL_OPT"
    assert "EPS_SCF 1e-6" in changed


def test_vasp_invalid_xml_falls_back_to_outcar(tmp_path):
    import ase

    fixture = Path(ase.__file__).parent / "test/testdata/vasp/OUTCAR_example_1"
    if not fixture.exists():
        pytest.skip("ASE 未附带官方样本")
    (tmp_path / "OUTCAR").write_bytes(fixture.read_bytes())
    (tmp_path / "vasprun.xml").write_text("<broken>")
    assert (
        module("structure/vasp_to_xyz.py").convert(tmp_path, tmp_path / "train.xyz")
        == 1
    )


def test_deepmd_to_ase_database_portable(tmp_path, atoms):
    import dpdata

    source = tmp_path / "deepmd"
    data = {
        "atom_names": ["Ge", "Te"],
        "atom_numbs": [1, 1],
        "atom_types": np.array([0, 1]),
        "orig": np.zeros(3),
        "cells": np.array([atoms.cell.array]),
        "coords": np.array([atoms.positions]),
        "energies": np.array([-3.0]),
        "forces": np.array([atoms.get_forces()]),
        "virials": np.array([np.eye(3) * 2]),
    }
    dpdata.LabeledSystem(data=data).to_deepmd_npy(str(source))
    output = tmp_path / "atoms.db"
    run("structure/deepmd_to_ase.py", source, "Ge", "Te", "-o", output)
    result = read(output)
    assert result.get_potential_energy() == -3
    np.testing.assert_allclose(result.get_forces(), atoms.get_forces())
    np.testing.assert_allclose(
        result.get_stress(voigt=False), -np.eye(3) * 2 / atoms.get_volume()
    )


def test_cif_conversion_sorts_elements(tmp_path, atoms):
    source = tmp_path / "cell.cif"
    write(source, atoms[::-1])
    output = tmp_path / "POSCAR"
    run("structure/convert_structure.py", source, output, "--sort-elements")
    assert read(output).get_chemical_symbols() == ["Ge", "Te"]


def test_phonon_bands_whitespace_and_last_band(tmp_path):
    source = tmp_path / "band.dat"
    source.write_text(
        "# phonopy\n# End points: 0.0 1.0\n 0.0   1.0\n 1.0   2.0\n\n\n0.0 -1.0\n1.0 0.5\n"
    )
    endpoints, bands = module("plotting/plot_phonon_band.py").load_bands(source)
    assert endpoints == [0.0, 1.0]
    assert len(bands) == 2 and bands[-1][-1] == [1.0, 0.5]
    run(
        "plotting/plot_phonon_band.py",
        source,
        "-o",
        tmp_path / "phon.png",
        "--labels",
        "G",
        "X",
    )
    assert (tmp_path / "phon.png").stat().st_size > 100


@pytest.mark.parametrize(
    "header", ["ML_LMLFF = .TRUE.\n", "free  energy ML TOTEN = -1.0\n"]
)
def test_export_rejects_machine_learning_labels(tmp_path, header):
    # 即使目录里有看似正常的输出，也不把混合来源的 MLFF 标签写成 DFT 数据。
    (tmp_path / "OUTCAR").write_text(header)
    output = tmp_path / "train.xyz"
    with pytest.raises(ValueError, match="MLFF"):
        module("structure/vasp_to_xyz.py").convert(tmp_path, output)
    assert not output.exists()
