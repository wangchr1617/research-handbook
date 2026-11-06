"""运行器的失效保护与真实输出检查：python -m unittest discover -s scripts/materials。"""

import argparse
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from ase import Atoms
from ase.calculators.singlepoint import SinglePointCalculator

from analyze_phase import coordination, drift_corrected_msd, partial_rdf, safe_radius
from record_startup import record, validate_receipt

from run_case import ROOT, Runner, controlled_md_stop, dump, incar_text, phase_change, restart_random_seed, vasp_result


class RunnerTests(unittest.TestCase):
    def args(self, path, **changes):
        values = dict(case="metal", output=path, resume=False, threads=1, config=None)
        values.update(changes)
        return argparse.Namespace(**values)

    def test_existing_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            sentinel = Path(d) / "keep.txt"
            sentinel.write_text("keep")
            with self.assertRaisesRegex(ValueError, "已存在"):
                Runner(self.args(Path(d)))
            self.assertEqual(sentinel.read_text(), "keep")

    def test_source_tree_cannot_receive_calculation_outputs(self):
        with self.assertRaisesRegex(ValueError, "_validation_runs"):
            Runner(self.args(ROOT / "examples/materials/should-not-exist"))

    def test_wrong_case_configuration_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "wrong.json"
            dump(cfg, {"case": "inorganic", "schema_version": 1})
            target = Path(d) / "new"
            with self.assertRaisesRegex(ValueError, "不匹配"):
                Runner(self.args(target, config=cfg))
            self.assertFalse(target.exists())

    def test_output_and_input_corruption_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            runner = Runner(self.args(Path(d) / "run"))
            cmd = [sys.executable, "-c", "from pathlib import Path; Path('curve.dat').write_text('1,2\\n')"]
            files = {"job.inp": "input", "POTCAR": b"test potential, not licensed data"}
            work = runner.task("probe", files, cmd)
            # 完成任务应被复用；后续给无效程序也不会重新启动计算。
            runner.task("probe", files, ["nonexistent-program"])
            (work / "curve.dat").write_text("changed")
            with self.assertRaisesRegex(ValueError, "输出指纹"):
                runner.task("probe", files, cmd)
            (work / "curve.dat").write_text("1,2\n")
            (work / "POTCAR").write_bytes(b"changed potential")
            with self.assertRaisesRegex(ValueError, "输入指纹"):
                runner.task("probe", {"job.inp": "input"}, cmd)

    def test_failed_process_is_not_marked_complete(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            runner = Runner(self.args(Path(d) / "run"))
            with self.assertRaises(subprocess.CalledProcessError):
                runner.task("failure", {"job.inp": "input"}, [sys.executable, "-c", "raise SystemExit(7)"])
            self.assertNotIn("failure", runner.records)

    def test_vasp_truncation_and_nelm_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "OUTCAR").write_text("unfinished")
            with self.assertRaisesRegex(ValueError, "未正常结束"):
                vasp_result(p)
            (p / "OUTCAR").write_text("General timing and accounting")
            (p / "vasprun.xml").write_text('<modeling><parameters><i name="NELM">2</i></parameters><calculation><scstep/><scstep/></calculation></modeling>')
            with self.assertRaisesRegex(ValueError, "NELM"):
                vasp_result(p)

    def test_incar_boolean_and_vector(self):
        text = incar_text({"lcalcpol": True, "lwave": False, "magmom": [2.5, -2.5]})
        self.assertIn("LCALCPOL = .TRUE.", text)
        self.assertIn("LWAVE = .FALSE.", text)
        self.assertIn("MAGMOM = 2.5 -2.5", text)


class PublishedResultsTests(unittest.TestCase):
    def diagnostic_receipt(self, case):
        path = ROOT / "_validation_runs/materials" / case / "startup.json"
        if not path.exists():
            self.skipTest("此检查需要本地运行诊断记录")
        return json.loads(path.read_text())

    def test_runtime_diagnostics_cannot_be_written_to_public_cases(self):
        with self.assertRaisesRegex(ValueError, "运行诊断须保存在"):
            record("phase-change", ROOT / "examples/materials/phase-change")

    def test_startup_evidence_cannot_be_promoted_or_lose_iterations(self):
        for case in ("phase-change", "electrocatalysis"):
            receipt = self.diagnostic_receipt(case)
            validate_receipt(receipt)
            invalid = copy.deepcopy(receipt)
            invalid["properties_complete"] = True
            with self.assertRaises(ValueError):
                validate_receipt(invalid)
            for key, value in (("ionic_steps", 0), ("max_scf_steps", 150), ("normal_end", False),
                               ("input_sha256", {}), ("composition", {})):
                invalid = copy.deepcopy(receipt)
                invalid["tasks"][next(iter(invalid["tasks"]))][key] = value
                with self.subTest(case=case, key=key), self.assertRaises(ValueError):
                    validate_receipt(invalid)

    def test_md_startup_requires_continuous_restart_evidence(self):
        receipt = self.diagnostic_receipt("phase-change")
        receipt["restart_input_matches_previous_CONTCAR"][0] = False
        with self.assertRaisesRegex(ValueError, "衔接"):
            validate_receipt(receipt)

    def test_published_csvs_contain_finite_actual_data(self):
        for path in (ROOT / "examples/materials").glob("*/data/curve.csv"):
            with self.subTest(path=path):
                self.assertTrue(np.isfinite(np.loadtxt(path, delimiter=",", skiprows=1)).all())
                metadata = json.loads(path.with_name("provenance.json").read_text())
                self.assertTrue(metadata["tasks"])
                for task in metadata["tasks"].values():
                    self.assertGreater(len(task["output_sha256"]), 0)

    def test_actual_mgo_output_energy_normalization(self):
        path = ROOT / "_validation_runs/materials/inorganic/volume-1.000"
        if not path.exists():
            self.skipTest("此检查需要本地实际 MgO 输出")
        result, frames, _ = vasp_result(path)
        csv = np.loadtxt(ROOT / "examples/materials/inorganic/data/curve.csv", delimiter=",", skiprows=1)
        index = np.argmin(abs(csv[:, 0] - frames[-1].get_volume()/2))
        self.assertAlmostEqual(csv[index, 1], result["E0_eV"]/2, places=9)

    def test_iron_magnetic_states_have_actual_projected_moments(self):
        path = ROOT / "examples/materials/magnetism/data/results.json"
        if not path.exists():
            self.skipTest("此检查需要实际 Fe 计算结果")
        states = json.loads(path.read_text())["states"]
        self.assertGreater(states["FM"]["total_moment_muB"], 3)
        self.assertTrue(all(m > 1 for m in states["FM"]["local_moments_muB"]))
        self.assertLess(abs(states["AFM"]["total_moment_muB"]), .1)
        a, b = states["AFM"]["local_moments_muB"]
        self.assertLess(a*b, 0)


class PhaseStatisticsTests(unittest.TestCase):
    def test_continuation_preserves_total_steps_and_temperature_ramp(self):
        class FakeRunner:
            def __init__(self, work):
                self.work = work
                self.config = json.loads((ROOT / "inputs/materials/phase-change.json").read_text())
                self.config["repeat"] = [1, 1, 1]
                self.config["stages"][0]["steps"] = 5
                self.config["stages"][1]["steps"] = 4
                self.config["stages"][2]["steps"] = 3
                self.args = argparse.Namespace(continue_md=True, publish=False)
                self.env = {}
                self.requests = []

            def vasp(self, name, atoms, mesh, settings, potentials, poscar, **kwargs):
                self.requests.append((name, settings.copy(), poscar))
                count = 2 if name in ("melt", "quench") else settings["nsw"]
                directory = self.work / name
                directory.mkdir()
                (directory / "CONTCAR").write_text(f"restart from {name}")
                (directory / "OSZICAR").write_text("T= 300.0\n"*count)
                (directory / "REPORT").write_text("RANDOM_SEED = 271828 384 0\n")
                frames = []
                for _ in range(count):
                    frame = atoms.copy()
                    frame.calc = SinglePointCalculator(frame, energy=-1.)
                    frames.append(frame)
                return {}, frames, ""

            def table(self, name, data, header):
                self.rows = np.array(data)

            def finish(self, result):
                self.result = result

        with tempfile.TemporaryDirectory() as d:
            runner = FakeRunner(Path(d))
            with patch("run_case.subprocess.run"):
                phase_change(runner)
            self.assertEqual([s[1]["nsw"] for s in runner.requests], [5, 3, 4, 2, 3])
            self.assertEqual(runner.requests[3][1]["tebeg"], 1150)
            self.assertEqual(runner.requests[1][1]["random_seed"], [271828, 384, 0])
            self.assertEqual(runner.requests[1][2], "restart from melt")
            self.assertEqual(len(runner.rows), 12)
            self.assertTrue(np.allclose(runner.rows[:, 0], np.arange(1, 13)*2))
            self.assertEqual(runner.result["time_fs"], 24)
            self.assertEqual(sum(s["steps"] for s in runner.result["phase_segments"]["melt"]), 5)

    def test_controlled_stop_and_restart_seed_are_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            self.assertFalse(controlled_md_stop(path))
            (path / "STOPCAR").write_text("LABORT = .TRUE.\n")
            self.assertFalse(controlled_md_stop(path))
            (path / "STOPCAR").write_text("LSTOP = .TRUE.\n")
            self.assertTrue(controlled_md_stop(path))
            (path / "REPORT").write_text("RANDOM_SEED = 271828 192 0\nRANDOM_SEED = 271828 384 0\n")
            self.assertEqual(restart_random_seed(path), [271828, 384, 0])
            (path / "REPORT").write_text("RANDOM_SEED = 271828 1000000 0\n")
            with self.assertRaisesRegex(ValueError, "范围"):
                restart_random_seed(path)
            (path / "STOPCAR").unlink()
            (path / "stdout.log").write_text("soft stop encountered!\ndeleting file STOPCAR\n")
            (path / "OUTCAR").write_text("aborting loop because EDIFF is reached\n")
            (path / "vasprun.xml").write_text("<modeling><calculation/></modeling>")
            self.assertTrue(controlled_md_stop(path))
            (path / "OUTCAR").write_text("unconverged")
            self.assertFalse(controlled_md_stop(path))

    def test_periodic_translation_does_not_create_internal_msd(self):
        a = Atoms("GeTe", positions=[[4.9, 1, 1], [1, 1, 1]], cell=[5, 5, 5], pbc=True)
        b = a.copy()
        b.positions += [0.2, 0, 0]
        b.wrap()
        self.assertTrue(np.allclose(drift_corrected_msd([a, b]), 0, atol=1e-20))

    def test_internal_motion_is_retained(self):
        a = Atoms("GeTe", positions=[[1, 1, 1], [2, 1, 1]], cell=[10, 10, 10], pbc=True)
        b = a.copy()
        b.positions[0, 0] += .1
        b.positions[1, 0] -= .1
        msd = drift_corrected_msd([a, b])
        self.assertTrue(np.all(msd[1] > 0))
        mass = a.get_masses()
        # 去掉质量加权质心后，两种位移幅度之比应与质量反比。
        self.assertAlmostEqual(np.sqrt(msd[1, 0]/msd[1, 1]), mass[1]/mass[0], places=10)

    def test_partial_rdf_pair_counts_and_self_exclusion(self):
        atoms = Atoms("GeGeTeTe", positions=[[0, 0, 0], [2, 0, 0], [1, 0, 0], [3, 0, 0]],
                      cell=[10, 10, 10], pbc=True)
        edges = np.linspace(0, 4, 9)
        rdf = partial_rdf([atoms], edges)
        shells = 4*np.pi/3*np.diff(edges**3)
        counts = np.sum(rdf*shells[:, None], axis=0)*np.array([2, 4, 2])/1000
        self.assertTrue(np.allclose(counts, [2, 4, 2]))
        self.assertTrue(np.all(rdf[0] == 0))

    def test_nonorthogonal_cell_uses_plane_spacing(self):
        cell = np.array([[4, 0, 0], [2, 3, 0], [0, 0, 5]])
        self.assertAlmostEqual(safe_radius(cell), 1.5)

    def test_invalid_sampling_geometry_is_rejected(self):
        atoms = Atoms("GeGeTeTe", positions=[[0, 0, 0], [1, 1, 0], [2, 1, 1], [3, 3, 3]],
                      cell=[5, 5, 5], pbc=True)
        with self.assertRaisesRegex(ValueError, "半径"):
            partial_rdf([atoms], np.linspace(0, 3, 10))
        with self.assertRaisesRegex(ValueError, "cutoff"):
            coordination([atoms], 2.6)
        changed = atoms.copy()
        changed.set_cell([6, 5, 5])
        with self.assertRaisesRegex(ValueError, "固定晶胞"):
            drift_corrected_msd([atoms, changed])


if __name__ == "__main__":
    unittest.main()
