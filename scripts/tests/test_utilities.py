"""独立实用工具行为回归：python -m unittest discover -s scripts/tests -p test_utilities.py。"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.io import read, write

SCRIPTS = Path(__file__).resolve().parents[1]


def load_rmse():
    spec = importlib.util.spec_from_file_location(
        "rmse_utility", SCRIPTS / "analysis/calculate_rmse.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UtilityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)

    def run_script(self, script, *args, cwd=None, env=None):
        command = ["/bin/bash"] if script.endswith(".sh") else [sys.executable]
        return subprocess.run(
            [*command, str(SCRIPTS / script), *map(str, args)],
            cwd=cwd or self.work,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_find_preview_then_delete_literal_names(self):
        names = [
            "with space",
            "with\nnewline\n",
            "-flag",
            "x; touch INJECTED",
            "$(touch INJECTED)",
        ]
        for name in names:
            (self.work / name).write_text("fixture")
        (self.work / "keep").write_text("keep")
        result = self.run_script("utils/remove_by_name.sh", "--", *names)
        self.assert_ok(result)
        self.assertTrue(all((self.work / name).exists() for name in names))
        result = self.run_script("utils/remove_by_name.sh", "--delete", "--", *names)
        self.assert_ok(result)
        self.assertFalse(any((self.work / name).exists() for name in names))
        self.assertEqual((self.work / "keep").read_text(), "keep")
        self.assertFalse((self.work / "INJECTED").exists())
        self.assertFalse((self.work / "name.sh").exists())

    def test_find_globs_directory_pruning_and_duplicates(self):
        target = self.work / "parent.tmp"
        target.mkdir()
        (target / "child.tmp").write_text("x")
        result = self.run_script(
            "utils/remove_by_name.sh", "--delete", "*.tmp", "parent.tmp"
        )
        self.assert_ok(result)
        self.assertIn("匹配 1 项", result.stdout)
        self.assertFalse(target.exists())
        self.assert_ok(self.run_script("utils/remove_by_name.sh", "missing"))

    def test_find_never_follows_symlinks_or_deletes_root(self):
        outside = self.work / "outside"
        outside.mkdir()
        (outside / "data.tmp").write_text("keep")
        root = self.work / "search.tmp\n"
        root.mkdir()
        (root / "alias.tmp").symlink_to(outside, target_is_directory=True)
        self.assert_ok(
            self.run_script(
                "utils/remove_by_name.sh", "--delete", "--root", root, "*.tmp"
            )
        )
        self.assertTrue(root.is_dir())
        self.assertEqual((outside / "data.tmp").read_text(), "keep")
        self.assertFalse((root / "alias.tmp").is_symlink())

    def test_find_rejects_invalid_arguments(self):
        for args in [
            (),
            ("--root",),
            ("--root", "/", "*"),
            ("a/b",),
            ("",),
            ("--delete", "--dry-run", "*"),
        ]:
            with self.subTest(args=args):
                self.assertEqual(
                    self.run_script("utils/remove_by_name.sh", *args).returncode, 2
                )

    def test_find_search_failure_does_not_start_deletion(self):
        (self.work / "keep.tmp").write_text("keep")
        tools = self.work / "bin"
        tools.mkdir()
        fake = tools / "find"
        fake.write_text('#!/bin/bash\nprintf "%s\\0" "$1/keep.tmp"\nexit 1\n')
        fake.chmod(0o755)
        result = self.run_script(
            "utils/remove_by_name.sh",
            "--delete",
            "*.tmp",
            env={**os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"]},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.work / "keep.tmp").read_text(), "keep")

    def make_tasks(self):
        for name in ("001", "002 with space", ".hidden"):
            (self.work / name).mkdir()

    def test_link_preview_create_and_idempotence(self):
        self.make_tasks()
        names = ["INCAR", "file with space", "line\nend\n", "-flag"]
        for name in names:
            (self.work / name).write_text(name)
        self.assert_ok(
            self.run_script(
                "utils/link_to_subdirectories.sh", "--dry-run", "--", *names
            )
        )
        self.assertFalse(list((self.work / "001").iterdir()))
        for _ in range(2):
            self.assert_ok(
                self.run_script("utils/link_to_subdirectories.sh", "--", *names)
            )
        for directory in ("001", "002 with space"):
            for name in names:
                p = self.work / directory / name
                self.assertTrue(p.is_symlink())
                self.assertEqual(os.readlink(p), "../" + name)
                self.assertEqual(p.read_text(), name)
        self.assertFalse(list((self.work / ".hidden").iterdir()))

    def test_link_conflict_is_preflighted_for_whole_batch(self):
        for kind in ("file", "directory", "broken", "wrong"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp)
                for name in ("a", "b"):
                    (work / name).mkdir()
                (work / "INCAR").write_text("original")
                conflict = work / "b/INCAR"
                if kind == "file":
                    conflict.write_text("keep")
                elif kind == "directory":
                    conflict.mkdir()
                else:
                    (work / "other").write_text("other")
                    conflict.symlink_to(
                        "../missing" if kind == "broken" else "../other"
                    )
                result = self.run_script(
                    "utils/link_to_subdirectories.sh", "INCAR", cwd=work
                )
                self.assertEqual(result.returncode, 2)
                self.assertFalse(list((work / "a").iterdir()))
                self.assertTrue(conflict.exists() or conflict.is_symlink())

    def test_link_external_source_and_directory_symlink(self):
        self.make_tasks()
        with tempfile.TemporaryDirectory() as tmp:
            external = Path(tmp)
            source = external / "input"
            source.write_text("external")
            (self.work / "alias").symlink_to(external, target_is_directory=True)
            self.assert_ok(self.run_script("utils/link_to_subdirectories.sh", source))
            self.assertEqual(
                os.readlink(self.work / "001/input"), str(source.resolve())
            )
            self.assertFalse((external / "input/input").exists())
            self.assertEqual(sorted(p.name for p in external.iterdir()), ["input"])

    def test_link_invalid_source_and_duplicate_basename(self):
        self.make_tasks()
        (self.work / "INCAR").write_text("x")
        result = self.run_script("utils/link_to_subdirectories.sh", "INCAR", "missing")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(list((self.work / "001").iterdir()))
        (self.work / "001/INCAR").write_text("different")
        self.assertEqual(
            self.run_script(
                "utils/link_to_subdirectories.sh", "INCAR", "001/INCAR"
            ).returncode,
            2,
        )
        self.assertEqual(
            self.run_script("utils/link_to_subdirectories.sh").returncode, 2
        )
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "INCAR").write_text("x")
            self.assertEqual(
                self.run_script(
                    "utils/link_to_subdirectories.sh", "INCAR", cwd=tmp
                ).returncode,
                2,
            )

    def test_rmse_component_definitions_and_single_row(self):
        module = load_rmse()
        for components, function in [
            (1, module.calculate_rmse_energy),
            (3, module.calculate_rmse_force),
            (6, module.calculate_rmse_virial),
        ]:
            for rows in (1, 4):
                with self.subTest(components=components, rows=rows):
                    data = (
                        np.arange(rows * components * 2, dtype=float).reshape(
                            rows, components * 2
                        )
                        / 100
                    )
                    path = self.work / "values"
                    np.savetxt(path, data)
                    expected = (
                        np.sqrt(
                            np.mean((data[:, :components] - data[:, components:]) ** 2)
                        )
                        * 1000
                    )
                    self.assertAlmostEqual(function(path), expected)

    def test_rmse_rejects_empty_missing_columns_and_nonfinite(self):
        module = load_rmse()
        for text in ("", "1\n", "nan 0\n", "inf 0\n", "a b\n"):
            (self.work / "values").write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                module.calculate_rmse_energy(self.work / "values")
        with self.assertRaises(OSError):
            module.calculate_rmse_force(self.work / "missing")

    def test_rmse_zero_and_large_values(self):
        module = load_rmse()
        path = self.work / "values"
        path.write_text("0 0\n")
        self.assertEqual(module.calculate_rmse_energy(path), 0)
        path.write_text("1e200 0\n")
        self.assertAlmostEqual(module.calculate_rmse_energy(path) / 1e203, 1)
        path.write_text("1e308 -1e308\n")
        with self.assertRaises(ValueError):
            module.calculate_rmse_energy(path)

    def test_rmse_cli_default_paths_and_failure_exit(self):
        for name, count in (("energy", 2), ("force", 6), ("virial", 12)):
            (self.work / f"{name}_train.out").write_text(" ".join(["0"] * count) + "\n")
        result = self.run_script("analysis/calculate_rmse.py")
        self.assert_ok(result)
        self.assertIn("Energy RMSE: 0.00 meV/atom", result.stdout)
        (self.work / "virial_train.out").unlink()
        result = self.run_script("analysis/calculate_rmse.py", "--directory", self.work)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_supercell_tilted_cell_and_element_counts(self):
        source = self.work / "inputs"
        source.mkdir()
        atoms = Atoms(
            "HeH",
            scaled_positions=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            cell=[[3, 0, 0], [1, 4, 0], [0.5, 0.2, 5]],
            pbc=True,
        )
        write(source / "POSCAR", atoms, format="vasp")
        self.assert_ok(
            self.run_script("structure/build_supercell.py", source / "POSCAR", 2, 1, 3)
        )
        output = source / "POSCAR_SC213.vasp"
        actual = read(output)
        self.assertEqual(len(actual), len(atoms) * 6)
        np.testing.assert_allclose(
            actual.cell, atoms.cell * np.array([2, 1, 3])[:, None]
        )
        self.assertAlmostEqual(actual.get_volume(), atoms.get_volume() * 6)
        self.assertEqual(actual.get_chemical_symbols(), ["H"] * 6 + ["He"] * 6)
        expected = atoms.repeat((2, 1, 3))
        actual_rows = sorted((a.symbol, *np.round(a.position, 10)) for a in actual)
        expected_rows = sorted((a.symbol, *np.round(a.position, 10)) for a in expected)
        self.assertEqual(actual_rows, expected_rows)
        original = output.read_bytes()
        self.assertNotEqual(
            self.run_script(
                "structure/build_supercell.py", source / "POSCAR", 2, 1, 3
            ).returncode,
            0,
        )
        self.assertEqual(output.read_bytes(), original)
        self.assert_ok(
            self.run_script(
                "structure/build_supercell.py",
                source / "POSCAR",
                1,
                1,
                1,
                "-o",
                self.work / "CUSTOM",
            )
        )
        np.testing.assert_allclose(
            read(self.work / "CUSTOM", format="vasp").cell, atoms.cell
        )

    def test_supercell_invalid_input_and_broken_output_link(self):
        source = self.work / "POSCAR"
        write(source, Atoms("H", cell=[3, 3, 3], pbc=True), format="vasp")
        for repeat in ((0, 1, 1), (-1, 2, 2), ("x", 1, 1)):
            self.assertNotEqual(
                self.run_script(
                    "structure/build_supercell.py", source, *repeat
                ).returncode,
                0,
            )
        target = self.work / "broken"
        target.symlink_to("missing")
        self.assertNotEqual(
            self.run_script(
                "structure/build_supercell.py", source, 1, 1, 1, "-o", target
            ).returncode,
            0,
        )
        source.write_text("not a structure")
        self.assertNotEqual(
            self.run_script("structure/build_supercell.py", source, 1, 1, 1).returncode,
            0,
        )
        self.assertFalse((self.work / "POSCAR_SC111.vasp").exists())

    def test_help_without_touching_files(self):
        for script in (
            "utils/remove_by_name.sh",
            "utils/link_to_subdirectories.sh",
            "structure/build_supercell.py",
            "analysis/calculate_rmse.py",
        ):
            self.assert_ok(self.run_script(script, "--help"))
        self.assertFalse(list(self.work.iterdir()))


if __name__ == "__main__":
    unittest.main()
