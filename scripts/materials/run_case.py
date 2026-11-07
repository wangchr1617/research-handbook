"""材料应用案例：python run_case.py CASE --output DIR [--resume] [--publish]。

输入取自 inputs/materials；仅调用已有本地程序。输出须置于仓库外或
_validation_runs 内；授权势只在运行目录拼接。--publish 只导出数值、输入指纹与图。
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import numpy as np
from ase import Atoms
from ase.build import bulk, fcc111, molecule
from ase.constraints import FixAtoms
from ase.io import read, write

ROOT = Path(__file__).resolve().parents[2]
CASES = ("metal", "inorganic", "organic", "semiconductor", "ferroelectric",
         "magnetism", "thermoelectric", "phase-change", "battery", "electrocatalysis")


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def incar_text(values):
    def value(x):
        if isinstance(x, bool):
            return ".TRUE." if x else ".FALSE."
        if isinstance(x, (list, tuple)):
            return " ".join(map(str, x))
        return str(x)
    return "\n".join(f"{key.upper()} = {value(v)}" for key, v in values.items()) + "\n"


def vasp_result(work):
    out = (work / "OUTCAR").read_text(errors="replace")
    if "General timing and accounting" not in out:
        raise ValueError(f"VASP 未正常结束：{work}")
    tree = ET.parse(work / "vasprun.xml").getroot()
    steps = tree.findall("calculation")
    nelm = int(tree.find(".//parameters//i[@name='NELM']").text)
    if not steps or any(len(s.findall("scstep")) >= nelm for s in steps):
        raise ValueError(f"电子迭代达到 NELM：{work}")
    energy = float(steps[-1].find("energy/i[@name='e_0_energy']").text)
    if not np.isfinite(energy):
        raise ValueError("能量非有限")
    frames = read(work / "vasprun.xml", index=":")
    forces = frames[-1].get_forces(apply_constraint=False)
    result = {"E0_eV": energy, "ionic_steps": len(steps),
              "max_scf_steps": max(len(s.findall("scstep")) for s in steps),
              "max_force_eV_A": float(np.linalg.norm(forces, axis=1).max()),
              "ionic_converged": "reached required accuracy" in out,
              "version": out.splitlines()[0].strip()}
    return result, frames, out


def controlled_md_stop(work):
    stop = work / "STOPCAR"
    requested = stop.is_file() and bool(re.search(
        r"^\s*LSTOP\s*=\s*(?:\.TRUE\.|TRUE|T)\s*(?:!.*)?$",
        stop.read_text(), flags=re.I | re.M))
    if requested:
        return True
    # VASP 6.5.1 处理正常停止后会删除 STOPCAR，需核对保留下来的日志证据。
    stdout = work / "stdout.log"
    if not stdout.is_file() or not (work / "OUTCAR").is_file():
        return False
    log = stdout.read_text(errors="replace")
    out = (work / "OUTCAR").read_text(errors="replace")
    if "soft stop encountered!" not in log or "deleting file STOPCAR" not in log:
        return False
    steps = ET.parse(work / "vasprun.xml").getroot().findall("calculation")
    return bool(steps) and out.count("aborting loop because EDIFF is reached") >= len(steps)


def restart_random_seed(work):
    report = (work / "REPORT").read_text()
    matches = re.findall(r"RANDOM_SEED\s*=\s*(\d+)\s+(\d+)\s+(\d+)", report)
    if not matches:
        raise ValueError("REPORT 中缺少可恢复的随机数状态")
    seed = list(map(int, matches[-1]))
    if not (0 <= seed[0] < 900000000 and 0 <= seed[1] < 1000000):
        raise ValueError("REPORT 的随机数状态超出范围")
    return seed


class Runner:
    def __init__(self, args):
        self.args = args
        config_path = args.config or ROOT / "inputs/materials" / (args.case + ".json")
        self.config = json.loads(config_path.read_text())
        if self.config.get("case") != args.case or self.config.get("schema_version") != 1:
            raise ValueError("配置中的 case 或 schema_version 不匹配")
        self.runner_hash = sha(Path(__file__))
        self.work = args.output.resolve()
        if self.work.is_relative_to(ROOT) and not self.work.is_relative_to(ROOT / "_validation_runs"):
            raise ValueError("仓库内运行目录须位于 _validation_runs，避免发布授权势或大输出")
        if self.work.exists() and not args.resume:
            raise ValueError("输出目录已存在；核对参数后用 --resume 或选择新目录")
        self.work.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ, OMP_NUM_THREADS=str(args.threads), OPENBLAS_NUM_THREADS="1",
                        VASP_OPENBLAS_NUM_THREADS="1", MPLCONFIGDIR=str(self.work / "mpl-cache"))
        os.environ["MPLCONFIGDIR"] = self.env["MPLCONFIGDIR"]
        os.environ["XDG_CACHE_HOME"] = str(self.work / "cache")
        self.records = {}
        if (self.work / "provenance.json").exists():
            old = json.loads((self.work / "provenance.json").read_text())
            if old["config"] != self.config:
                raise ValueError("续跑配置与原运行不一致，请换新目录")
            self.records = old["tasks"]

    def record(self, name, work, cmd, seconds):
        inputs = {f.name: sha(f) for f in work.iterdir() if f.name in
                  ("INCAR", "POSCAR", "KPOINTS", "POTCAR", "CHGCAR", "job.inp", "in.lammps", "Al_mm.eam.fs")}
        outputs = {f.name: sha(f) for f in work.iterdir() if f.name in
                   ("OUTCAR", "vasprun.xml", "CONTCAR", "stdout.log", "log.lammps", "curve.dat")}
        self.records[name] = {"command": cmd, "seconds": round(seconds, 3),
                              "input_sha256": inputs, "output_sha256": outputs}
        dump(self.work / "provenance.json", {"config": self.config, "tasks": self.records,
             "runner_sha256": self.runner_hash, "platform": platform.system(), "machine": platform.machine()})

    def task(self, name, files, cmd):
        work = self.work / name
        work.mkdir(exist_ok=True)
        for filename, content in files.items():
            target = work / filename
            data = content if isinstance(content, bytes) else content.encode()
            if target.exists() and target.read_bytes() != data:
                raise ValueError(f"已有任务输入不一致：{target}")
            target.write_bytes(data)
        if name in self.records:
            for filename, digest in self.records[name]["input_sha256"].items():
                if sha(work / filename) != digest:
                    raise ValueError(f"续跑输入指纹不一致：{work / filename}")
            for filename, digest in self.records[name]["output_sha256"].items():
                if sha(work / filename) != digest:
                    raise ValueError(f"续跑输出指纹不一致：{work / filename}")
            return work
        executable = shutil.which(cmd[0])
        if not executable:
            raise FileNotFoundError(f"未安装或未加入 PATH：{cmd[0]}；本脚本不会安装软件")
        start = time.monotonic()
        print("START", self.args.case, name, flush=True)
        with (work / "stdout.log").open("w") as log:
            subprocess.run(cmd, cwd=work, env=self.env, stdout=log, stderr=subprocess.STDOUT, check=True)
        self.record(name, work, cmd, time.monotonic() - start)
        print("END", name, round(time.monotonic() - start, 1), flush=True)
        return work

    def vasp(self, name, atoms, mesh=(5, 5, 5), settings=None, potnames=None, poscar=None,
             allow_short_md=False):
        base = dict(encut=450, prec="Accurate", ediff=1e-7, nelm=150, algo="Normal",
                    ismear=0, sigma=0.05, lreal=False, lwave=False, lcharg=False,
                    ibrion=-1, nsw=0, isym=0, ncore=1)
        base.update(settings or {})
        if potnames is None:
            potnames = list(dict.fromkeys(atoms.get_chemical_symbols()))
        if poscar is None:
            stream = io.StringIO()
            write(stream, atoms, format="vasp", direct=True, sort=False)
            poscar = stream.getvalue()
        potentials = b"".join((self.args.potential_root / e / "POTCAR").read_bytes() for e in potnames)
        cmd = [self.args.vasp]
        if self.args.ranks > 1:
            cmd = ["mpirun", "--oversubscribe", "--bind-to", "none", "-np", str(self.args.ranks)] + cmd
        work = self.task(name, {"INCAR": incar_text(base), "POSCAR": poscar,
                               "KPOINTS": "mesh\n0\nGamma\n" + " ".join(map(str, mesh)) + "\n0 0 0\n",
                               "POTCAR": potentials}, cmd)
        result, frames, out = vasp_result(work)
        if base.get("ibrion") in (1, 2) and not result["ionic_converged"]:
            raise ValueError(f"结构优化未收敛：{work}")
        if base.get("ibrion") == 0 and len(frames) != base["nsw"]:
            if not (allow_short_md and 0 < len(frames) < base["nsw"] and controlled_md_stop(work)):
                raise ValueError("MD 步数不足，且没有启用有效的正常停止续算")
            self.records[name]["controlled_stop"] = {
                "requested_steps": base["nsw"], "completed_steps": len(frames),
                "STOPCAR_sha256": sha(work / "STOPCAR") if (work / "STOPCAR").exists() else None,
                "normal_stop_stdout_sha256": sha(work / "stdout.log")}
        return result, frames, out

    def table(self, name, data, header):
        np.savetxt(self.work / name, np.asarray(data), delimiter=",", header=header, comments="")

    def finish(self, result):
        dump(self.work / "results.json", result)
        plot_case(self.args.case, self.work)
        provenance_path = self.work / "provenance.json"
        provenance = json.loads(provenance_path.read_text())
        provenance["analysis_runner_sha256"] = self.runner_hash
        provenance["analysis_python"] = platform.python_version()
        provenance["derived_sha256"] = {name: sha(self.work / name)
                                         for name in ("results.json", "curve.csv", "result.png")}
        dump(provenance_path, provenance)
        if self.args.publish:
            target = ROOT / "examples/materials" / self.args.case / "data"
            target.mkdir(parents=True, exist_ok=True)
            for name in ("results.json", "provenance.json", "curve.csv", "result.png"):
                if (self.work / name).exists():
                    shutil.copy2(self.work / name, target / name)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


def phase_change(r):
    c = r.config
    atoms = bulk("GeTe", "rocksalt", a=c["a_A"]).repeat(c["repeat"])
    # 将同元素排成连续块，保持 POSCAR 与两个 PAW 势的顺序一致。
    atoms = atoms[np.argsort(atoms.numbers, kind="stable")]
    crystal = atoms.copy()
    atoms.rattle(c["rattle_A"], seed=c["seed"])
    settings = dict(encut=c["encut_eV"], prec="Normal", ediff=1e-5, ismear=0, sigma=0.1,
                    ibrion=0, mdalgo=3, langevin_gamma=[10, 10], random_seed=[c["seed"], 0, 0],
                    potim=c["dt_fs"], isif=2, addgrid=True)
    rows = []
    poscar = None
    elapsed = 0.0
    all_frames = []
    phase_segments = {}
    for index, stage in enumerate(c["stages"]):
        done, chunk = 0, 0
        seed = settings["random_seed"]
        phase_segments[stage["name"]] = []
        while done < stage["steps"]:
            name = stage["name"] if chunk == 0 else f"{stage['name']}-continue-{chunk:03d}"
            start = stage["start_K"] if done == 0 else stage["start_K"] + (stage["end_K"]-stage["start_K"])*done/stage["steps"]
            st = dict(settings, nsw=stage["steps"]-done, tebeg=start, teend=stage["end_K"], random_seed=seed)
            _, frames, _ = r.vasp(name, atoms, (1, 1, 1), st, ["Ge", "Te"], poscar,
                                  allow_short_md=r.args.continue_md)
            # CONTCAR 原样衔接，保留速度和预测校正信息；短段只补足剩余步数。
            work = r.work / name
            poscar = (work / "CONTCAR").read_text()
            temps = re.findall(r"\bT=\s*([\d.E+\-]+)", (work / "OSZICAR").read_text())
            if len(temps) != len(frames):
                raise ValueError("OSZICAR 温度行数与轨迹不符")
            for j, (frame, temp) in enumerate(zip(frames, temps)):
                rows.append([elapsed + (j+1)*c["dt_fs"], index, float(temp),
                             frame.get_potential_energy()/len(frame)])
            elapsed += len(frames)*c["dt_fs"]
            all_frames.extend(frames)
            phase_segments[stage["name"]].append({"task": name, "steps": len(frames)})
            done += len(frames)
            if done < stage["steps"]:
                seed = restart_random_seed(work)
            chunk += 1
            dump(r.work / "phase-segments.json", phase_segments)
    r.table("curve.csv", rows, "time_fs,stage,temperature_K,potential_energy_eV_atom")
    initial = crystal.get_all_distances(mic=True)
    final = all_frames[-1].get_all_distances(mic=True)
    np.fill_diagonal(initial, np.inf)
    np.fill_diagonal(final, np.inf)
    cutoff = c["coordination_cutoff_A"]
    r.finish({"atoms": len(atoms), "time_fs": elapsed, "temperature_stages": c["stages"],
              "phase_segments": phase_segments,
              "initial_mean_coordination": float((initial < cutoff).sum(axis=1).mean()),
              "final_mean_coordination": float((final < cutoff).sum(axis=1).mean()),
              "minimum_distance_A": float(final.min()),
              "final_temperature_K": rows[-1][2],
              "interpretation": "有限尺寸短轨迹的熔融—淬火—退火流程；非晶形成和晶化须由更长、多初态统计另行判断"})
    # 轨迹只在本地运行目录保留，公开资料导出统计量。
    write(r.work / "trajectory.extxyz", all_frames)
    command = [sys.executable, str(Path(__file__).with_name("analyze_phase.py")), str(r.work)]
    if r.args.publish:
        command.append("--publish")
    subprocess.run(command, env=r.env, check=True)


def inorganic(r):
    c = r.config
    reference = bulk("MgO", "rocksalt", a=c["a_A"])
    rows = []
    for factor in c["volume_factors"]:
        atoms = reference.copy()
        atoms.set_cell(reference.cell * factor ** (1 / 3), scale_atoms=True)
        result, _, _ = r.vasp(f"volume-{factor:.3f}", atoms, tuple(c["kmesh"]),
                              {"encut": c["encut_eV"]})
        rows.append([atoms.get_volume() / len(atoms), result["E0_eV"] / len(atoms)])
    from ase.eos import EquationOfState
    v0, e0, b = EquationOfState(*np.array(rows).T, eos="birchmurnaghan").fit()
    r.table("curve.csv", rows, "volume_A3_atom,E0_eV_atom")
    r.finish({"equilibrium_volume_A3_atom": float(v0), "E0_eV_atom": float(e0),
              "bulk_modulus_GPa": float(b * 160.21766208), "model": "MgO rocksalt; PBE; static 0 K EOS"})


def metal(r):
    c = r.config
    potential = r.args.lammps_potentials / "Al_mm.eam.fs"
    inp = f"""units metal
atom_style atomic
boundary p p p
lattice fcc {c['a_A']}
region box block 0 4 0 4 0 4
create_box 1 box
create_atoms 1 box
mass 1 26.9815385
pair_style eam/fs
pair_coeff * * Al_mm.eam.fs Al
neighbor 2.0 bin
thermo 10
thermo_style custom step pe press vol
fix relax all box/relax iso 0.0 vmax 0.001
minimize 1.0e-12 1.0e-10 1000 10000
unfix relax
variable v0 equal $(vol)
variable l0 equal $(lx)
variable lxval equal lx
variable epa equal pe/count(all)
variable pressure equal press
print "strain,energy_eV_atom,pressure_bar" file curve.dat screen no
variable i loop 11
label loop
variable strain equal -0.025+(v_i-1)*0.005
variable newlen equal v_l0*(1+v_strain)
change_box all x final 0 ${{newlen}} y final 0 ${{newlen}} z final 0 ${{newlen}} remap units box
minimize 1.0e-12 1.0e-10 1000 10000
print "${{strain}},${{epa}},${{pressure}}" append curve.dat screen no
next i
jump SELF loop
"""
    w = r.task("Al-EOS", {"in.lammps": inp, "Al_mm.eam.fs": potential.read_bytes()},
               [r.args.lammps, "-in", "in.lammps"])
    if "Total wall time:" not in (w / "stdout.log").read_text():
        raise ValueError("LAMMPS 未结束")
    data = np.loadtxt(w / "curve.dat", delimiter=",", skiprows=1)
    r.table("curve.csv", data, "linear_strain,energy_eV_atom,pressure_bar")
    r.finish({"atoms": 256, "minimum_sampled_energy_eV_atom": float(data[:, 1].min()),
              "potential": "Al_mm.eam.fs", "model": "classical EAM; uniform hydrostatic strain; zero-temperature minimization"})


def organic(r):
    c = r.config
    # ASE 自带乙醇坐标，用两个 C-C-O-H 二面角构造构象初态。
    base = molecule("CH3CH2OH")
    symbols = base.get_chemical_symbols()
    oxygen = symbols.index("O")
    carbons = [i for i, el in enumerate(symbols) if el == "C"]
    near = min(carbons, key=lambda i: base.get_distance(i, oxygen))
    far = next(i for i in carbons if i != near)
    hydrogen = min((i for i, el in enumerate(symbols) if el == "H"), key=lambda i: base.get_distance(i, oxygen))
    rows, results = [], {}
    for label, angle in c["dihedral_deg"].items():
        atoms = base.copy()
        atoms.set_dihedral(far, near, oxygen, hydrogen, angle, indices=[hydrogen])
        coords = "\n".join(f"{s} {x:.10f} {y:.10f} {z:.10f}" for s, (x, y, z) in zip(symbols, atoms.positions))
        inp = f"! {c['method']} def2-SVP TightSCF TightOpt Opt Freq\n%maxcore 1000\n* xyz 0 1\n{coords}\n*\n"
        w = r.task(label, {"job.inp": inp}, [r.args.orca, "job.inp"])
        text = (w / "stdout.log").read_text()
        if "ORCA TERMINATED NORMALLY" not in text or "THE OPTIMIZATION HAS CONVERGED" not in text:
            raise ValueError("ORCA 结束或优化判据未通过")
        energy = float(re.findall(r"FINAL SINGLE POINT ENERGY\s+([-\d.]+)", text)[-1])
        freqs = [float(x) for x in re.findall(r"\d+:\s+([-\d.]+)\s+cm\*\*-1", text)]
        if len(freqs) != 3 * len(atoms) or min(freqs) < -20:
            raise ValueError("频率数不完整或有显著虚频")
        gibbs = float(re.findall(r"Final Gibbs free energy\s+\.\.\.\s+([-\d.]+)", text)[-1])
        final = read(w / "job.xyz")
        results[label] = {"energy_Ha": energy, "G_Ha": gibbs,
                          "minimum_frequency_cm-1": min(freqs),
                          "final_dihedral_deg": final.get_dihedral(far, near, oxygen, hydrogen)}
        rows.append([angle, energy * 27.211386245988, gibbs * 27.211386245988])
    data = np.array(rows)
    data[:, 1:] -= data[:, 1:].min(axis=0)
    r.table("curve.csv", data, "initial_dihedral_deg,relative_E_eV,relative_G_eV")
    r.finish({"conformers": results, "method": c["method"] + "/def2-SVP", "G_temperature_K": 298.15,
              "interpretation": "气相构象自由能比较；低频热化学模型以 ORCA 输出为准，未另做受阻转子或构象简并度修正"})


def semiconductor(r):
    c = r.config
    atoms = bulk("Si", "diamond", a=c["a_A"])
    result, _, _ = r.vasp("scf", atoms, tuple(c["kmesh"]), {"lcharg": True})
    from ase.dft.kpoints import bandpath
    path = bandpath("GXWKGLUWLK,UX", atoms.cell, npoints=70)
    # 能带任务使用显式点列；继承已收敛电荷，不能将线模式当成自洽积分网格。
    w = r.work / "scf"
    settings = dict(encut=450, prec="Accurate", ediff=1e-7, nelm=150, algo="Normal", ismear=0,
                    sigma=0.05, lreal=False, lwave=False, lcharg=False, ibrion=-1, nsw=0, isym=0,
                    icharg=11, lorbit=11)
    kpoints = "path\n" + str(len(path.kpts)) + "\nReciprocal\n" + "\n".join(
        " ".join(map(str, p)) + " 1" for p in path.kpts) + "\n"
    files = {"INCAR": incar_text(settings), "POSCAR": (w / "POSCAR").read_text(),
             "KPOINTS": kpoints, "POTCAR": (w / "POTCAR").read_bytes(),
             "CHGCAR": (w / "CHGCAR").read_bytes()}
    cmd = [r.args.vasp]
    work = r.task("bands", files, cmd)
    vasp_result(work)
    bands = read(work / "vasprun.xml")
    eigen = np.array([bands.calc.get_eigenvalues(kpt=k) for k in range(len(path.kpts))])
    occ = np.array([bands.calc.get_occupation_numbers(kpt=k) for k in range(len(path.kpts))])
    vbm = float(eigen[occ > 1].max())
    cbm = float(eigen[occ < 1].min())
    x, ticks, labels = path.get_linear_kpoint_axis()
    r.table("curve.csv", np.column_stack([x, eigen - vbm]), "distance_invA," + ",".join(f"band{i}_eV" for i in range(eigen.shape[1])))
    r.finish({"E0_eV": result["E0_eV"], "path_gap_eV": cbm - vbm,
              "kpath": path.path, "path_ticks_invA": ticks.tolist(), "path_labels": labels,
              "model": "Si PBE; line-path sampled gap, not a converged fundamental gap"})


def ferroelectric(r):
    c = r.config
    # 中心对称四方参考与一个反演奇的极性畸变模，端点不是预先认定的极小值。
    positions = np.array([[0, 0, 0], [.5, .5, .5], [.5, .5, 0], [.5, 0, .5], [0, .5, .5]])
    mode = np.array([0., 0.12, -0.04, -0.06, -0.06])
    rows = []
    for q in c["amplitudes"]:
        atoms = Atoms("BaTiOOO", scaled_positions=positions, cell=[c["a_A"], c["a_A"], c["c_A"]], pbc=True)
        atoms.positions[:, 2] += q * mode
        result, frames, out = r.vasp(f"q-{q:+.2f}", atoms, tuple(c["kmesh"]),
                                {"encut": c["encut_eV"], "lcalcpol": True}, ["Ba_sv", "Ti_sv", "O"])
        calc = frames[-1].calc
        eig = np.concatenate([calc.get_eigenvalues(kpt=k) for k in range(len(calc.get_ibz_k_points()))])
        occ = np.concatenate([calc.get_occupation_numbers(kpt=k) for k in range(len(calc.get_ibz_k_points()))])
        if np.any((occ > .01) & (occ < 1.99)) or eig[occ < 1].min() <= eig[occ > 1].max():
            raise ValueError("极化路径出现非绝缘占据，不能沿用 Berry 相分析")
        ion = re.findall(r"p\[ion\]=\s*\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", out)
        ele = re.findall(r"p\[elc\]=\s*\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", out)
        if not ion or not ele:
            raise ValueError("缺少 Berry 相偶极输出")
        dip = float(ion[-1][2]) + float(ele[-1][2])
        rows.append([q, result["E0_eV"], dip])
    data = np.array(rows)
    quantum = c["c_A"]
    dipoles = np.unwrap(data[:, 2] * 2 * np.pi / quantum) * quantum / (2 * np.pi)
    center = int(np.argmin(abs(data[:, 0])))
    data[:, 1] -= data[center, 1]
    data[:, 2] = (dipoles - dipoles[center]) * 16.02176634 / (c["a_A"]**2 * c["c_A"])
    r.table("curve.csv", data, "mode_amplitude,delta_energy_eV_cell,delta_Pz_C_m2")
    r.finish({"reference": "centrosymmetric tetragonal BaTiO3; fixed cell and prescribed polar mode",
              "polarization_quantum_C_m2": 16.02176634 / c["a_A"]**2,
              "energy_inversion_error_eV": float(np.max(abs(data[:, 1] - data[::-1, 1]))),
              "polarization_inversion_error_C_m2": float(np.max(abs(data[:, 2] + data[::-1, 2]))),
              "interpretation": "绝缘路径的能量与极化扫描；极小值、真实翻转势垒及电滞回线需另行求解"})


def magnetism(r):
    c = r.config
    atoms = bulk("Fe", "bcc", a=c["a_A"], cubic=True)
    rows = []
    results = {}
    for name, moments in {"NM": None, "FM": [2.5, 2.5], "AFM": [2.5, -2.5]}.items():
        settings = dict(encut=c["encut_eV"], ismear=1, sigma=0.1, ispin=1 if moments is None else 2)
        if moments:
            settings["magmom"] = moments
            settings["lorbit"] = 11
        result, frames, out = r.vasp(name, atoms, tuple(c["kmesh"]), settings)
        moment, local = 0.0, [0.0, 0.0]
        if moments is not None:
            total = re.findall(r"number of electron\s+[-\d.]+\s+magnetization\s+([-\d.]+)", out)
            if not total or "magnetization (x)" not in out:
                raise ValueError("自旋计算缺少总磁矩或局域磁矩输出")
            moment = float(total[-1])
            block = out.rsplit("magnetization (x)", 1)[1]
            local = []
            for line in block.splitlines():
                match = re.match(r"\s*(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*$", line)
                if match:
                    local.append(float(match[5]))
                if len(local) == len(atoms):
                    break
            if len(local) != len(atoms):
                raise ValueError("局域磁矩行数与原子数不符")
        results[name] = dict(result, total_moment_muB=moment, local_moments_muB=local)
        rows.append([len(rows), result["E0_eV"] / 2, moment / 2])
    data = np.array(rows)
    data[:, 1] -= data[:, 1].min()
    r.table("curve.csv", data, "state_NM_FM_AFM,relative_energy_eV_atom,net_moment_muB_atom")
    r.finish({"states": results, "model": "bcc Fe, same fixed cell, PBE collinear states; local moments depend on projection"})


def battery(r):
    c = r.config
    from ase.build import graphene
    # √3×√3 R30° 的 C6 单层；每周期放一个 Li，代表 stage-I LiC6。
    from ase.build import make_supercell
    host = graphene(a=c["graphene_a_A"], vacuum=1)
    hollow_xy = np.array([1/3, 2/3, 0]) @ host.cell.array
    host = make_supercell(host, np.array([[1, -1, 0], [1, 2, 0], [0, 0, 1]]))
    host.set_cell([*host.cell[:2], [0, 0, c["lic6_c_A"]]], scale_atoms=False)
    host.positions[:, 2] = 0
    lic = host.copy()
    lic += Atoms("Li", positions=[[hollow_xy[0], hollow_xy[1], .5*c["lic6_c_A"]]], cell=host.cell, pbc=True)
    # AB 石墨独立参考；LiC6 为 AA 层间结构，不能把两者层间距强行设成相同。
    graphite = Atoms("CCCC", scaled_positions=[[0, 0, .25], [1/3, 2/3, .25], [0, 0, .75], [2/3, 1/3, .75]],
                      cell=[[c["graphene_a_A"], 0, 0], [-c["graphene_a_A"]/2, c["graphene_a_A"]*np.sqrt(3)/2, 0], [0, 0, c["graphite_c_A"]]], pbc=True)
    li = bulk("Li", "bcc", a=c["li_a_A"], cubic=True)
    energies, counts = {}, {}
    for name, atoms, mesh in [("graphite", graphite, (9, 9, 5)), ("LiC6", lic, (5, 5, 5)), ("Li-metal", li, (9, 9, 9))]:
        result, frames, _ = r.vasp(name, atoms, mesh,
            {"encut": c["encut_eV"], "ivdw": 12, "ibrion": 2, "nsw": 100, "ediffg": -0.02, "isif": 2})
        energies[name] = result["E0_eV"]
        counts[name] = len(frames[-1])
    delta = energies["LiC6"] - 1.5*energies["graphite"] - .5*energies["Li-metal"]
    capacity = 96485.33212 / (3.6 * 6 * 12.011)
    r.table("curve.csv", [[0, 0], [1, delta]], "x_in_LixC6,formation_energy_eV_C6")
    r.finish({"energies_eV_cell": energies, "atom_counts": counts, "insertion_energy_eV_Li": delta,
              "average_voltage_V_vs_Li": -delta, "capacity_mAh_g_graphite": capacity,
              "model": "fixed-cell PBE-D3(BJ), relaxed internal coordinates; graphite-host mass normalization; endpoint voltage only"})


def electrocatalysis(r):
    c = r.config
    from ase.build import add_adsorbate
    slab = fcc111("Pt", size=(2, 2, 3), a=c["pt_a_A"], vacuum=8., orthogonal=True)
    slab.set_constraint(FixAtoms(mask=slab.get_tags() > 1))
    ads = slab.copy()
    add_adsorbate(ads, "H", 1.0, "fcc")
    h2 = molecule("H2")
    h2.center(vacuum=5.)
    results, structures = {}, {}
    for name, atoms, mesh in [("clean", slab, (3, 3, 1)), ("H-ads", ads, (3, 3, 1)), ("H2", h2, (1, 1, 1))]:
        settings = dict(encut=c["encut_eV"], ediff=1e-7, ibrion=2, nsw=100, ediffg=-0.02, isif=2)
        if name != "H2":
            settings.update(ldipol=True, idipol=3, dipol=[.5, .5, .5])
        result, frames, _ = r.vasp(name, atoms, mesh, settings)
        results[name] = result
        structures[name] = frames[-1]
    frequencies = {}
    for name, structure, mesh in [("H-ads", structures["H-ads"], (3, 3, 1)), ("H2", structures["H2"], (1, 1, 1))]:
        structure.set_constraint(FixAtoms(mask=[s != "H" for s in structure.get_chemical_symbols()]))
        settings = {"encut": c["encut_eV"], "ediff": 1e-8, "ibrion": 5, "nfree": 2,
                    "potim": .015, "nsw": 1, "isif": 2}
        if name == "H-ads":
            settings.update(ldipol=True, idipol=3, dipol=[.5, .5, .5])
        _, _, out = r.vasp(name + "-freq", structure, mesh, settings)
        values = [float(x) for x in re.findall(r"f\s*=.*?([-\d.]+)\s+cm-1", out)]
        imaginary = [float(x) for x in re.findall(r"f/i\s*=.*?([-\d.]+)\s+cm-1", out)]
        if any(x > 100 for x in imaginary):
            raise ValueError("吸附构型或分子含显著虚频")
        frequencies[name] = values
    eads = results["H-ads"]["E0_eV"] - results["clean"]["E0_eV"] - .5*results["H2"]["E0_eV"]
    conversion = 1.239841984e-4  # cm^-1 转 eV。
    zpe_ads = .5*conversion*sum(frequencies["H-ads"])
    zpe_h2 = .5*conversion*max(frequencies["H2"])
    ts_half = .5*c["temperature_K"]*c["H2_entropy_J_mol_K"]/96485.33212
    dg = eads + zpe_ads - .5*zpe_h2 + ts_half
    rows = [[u, 0, dg+u, 2*u] for u in c["potentials_V_RHE"]]
    r.table("curve.csv", rows, "U_V_RHE,initial_eV,Hstar_eV,final_eV")
    r.finish({"energies": results, "frequencies_cm-1": frequencies,
              "adsorption_energy_eV_H": eads, "ZPE_ads_eV": zpe_ads, "ZPE_H2_eV": zpe_h2,
              "half_TS_H2_eV": ts_half, "delta_G_H_eV": dg,
              "coverage_ML": .25, "surface": "Pt(111); bottom two layers fixed; three-layer slab",
              "approximation": "CHE vs RHE, ideal gas H2 entropy at 1 bar, no adsorbate vibrational entropy or solvent; partial H-only Hessian"})


def thermoelectric(r):
    c = r.config
    atoms = bulk("Si", "diamond", a=c["a_A"])
    r.vasp("scf", atoms, tuple(c["kmesh"]), {"encut": 450})
    w = r.work / "scf"
    # 采用已安装的 BoltzTraP2 命令，不触发 pip 或其他软件安装。
    for cmd, logfile in [([r.args.btp2, "-n", "1", "interpolate", "-m", "3", "."], "interpolate.log"),
                         ([r.args.btp2, "-n", "1", "integrate", "-b", "1000", "interpolation.bt2", "300,600"], "integrate.log")]:
        with (w / logfile).open("w") as out:
            subprocess.run(cmd, cwd=w, env=r.env, stdout=out, stderr=subprocess.STDOUT, check=True)
    from BoltzTraP2.serialization import load_results
    from ase.units import Hartree, Rydberg
    bt = load_results(w / "interpolation.btj")
    reference = float(bt[1] * Hartree)
    data = np.loadtxt(w / "interpolation.trace")
    data[:, 0] = data[:, 0]*Rydberg-reference
    selected = data[np.abs(data[:, 0]) < .8]
    pf = selected[:, 4]**2*selected[:, 5]
    r.table("curve.csv", np.column_stack([selected[:, 0], selected[:, 1], selected[:, 4]*1e6,
            selected[:, 5], selected[:, 7], pf]),
            "mu_minus_ref_eV,T_K,S_uV_K,sigma_over_tau_S_m_s,kappae_over_tau_W_m_K_s,PF_over_tau_W_m_K2_s")
    if not np.isfinite(selected).all():
        raise ValueError("输运系数非有限")
    r.finish({"reference_energy_eV": reference, "rows": len(selected),
              "scattering_model": bt[-1]["scattering_model"], "BoltzTraP2_version": bt[-1]["program_version"],
              "model": "Si PBE, constant relaxation time; chemical-potential scan; absolute tau and ZT not inferred"})


def plot_case(case, work, output=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    data = np.loadtxt(work / "curve.csv", delimiter=",", skiprows=1, ndmin=2)
    fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    if case == "phase-change":
        ax.plot(data[:, 0]/1000, data[:, 2], lw=.8)
        ax.set(xlabel="Time (ps)", ylabel="Temperature (K)")
    elif case == "ferroelectric":
        ax.plot(data[:, 0], data[:, 1]*1000, "o-", label="Energy")
        ax.set(xlabel="Polar-mode amplitude", ylabel="Energy relative to q=0 (meV/cell)")
        twin = ax.twinx()
        twin.plot(data[:, 0], data[:, 2], "s--", color="tab:orange")
        twin.set_ylabel("Polarization change (C/m$^2$)")
    elif case == "semiconductor":
        # 不连接路径中逗号分开的两段，也不把它画成真实的垂直色散。
        disconnected = np.where(np.diff(data[:, 0]) < 1e-10)[0] + 1
        plotted = np.insert(data, disconnected, np.nan, axis=0)
        ax.plot(plotted[:, 0], plotted[:, 1:], color="tab:blue", lw=.8)
        metadata = json.loads((work / "results.json").read_text())
        if "path_ticks_invA" in metadata:
            ticks, labels = [], []
            for position, label in zip(metadata["path_ticks_invA"], metadata["path_labels"]):
                label = "$\\Gamma$" if label == "G" else label
                if ticks and np.isclose(position, ticks[-1]):
                    labels[-1] += "|" + label
                else:
                    ticks.append(position)
                    labels.append(label)
                    ax.axvline(position, color="0.8", lw=.6)
            ax.set_xticks(ticks, labels)
        ax.set(xlabel="k path (distance in $\\AA^{-1}$)", ylabel="Energy relative to path VBM (eV)", ylim=(-6, 7))
    elif case == "thermoelectric":
        for temperature in np.unique(data[:, 1]):
            d = data[data[:, 1] == temperature]
            ax.plot(d[:, 0], d[:, 2], label=f"{temperature:g} K")
        ax.set(xlabel="Chemical potential relative to reference (eV)", ylabel="Seebeck coefficient ($\\mu$V/K)")
        ax.legend()
    elif case == "electrocatalysis":
        for row in data:
            for x, energy in enumerate(row[1:]):
                ax.hlines(energy, x-.22, x+.22, color="tab:blue" if row[0] == 0 else "tab:orange")
            ax.plot(range(3), row[1:], "--", label=f"U={row[0]:g} V vs RHE")
        ax.set(xticks=range(3), xticklabels=["2(H+ + e-) + *", "H* + H+ + e-", "H2 + *"], ylabel="Free energy (eV)")
        ax.legend()
    elif case == "organic":
        x = np.arange(len(data))
        ax.bar(x-.18, data[:, 1]*1000, width=.36, label="Electronic E")
        ax.bar(x+.18, data[:, 2]*1000, width=.36, label="ORCA G")
        ax.set(xticks=x, xticklabels=[f"Initial {a:g} deg" for a in data[:, 0]],
               ylabel="Relative energy (meV/molecule)")
        ax.legend()
    elif case == "magnetism":
        ax.bar(["NM", "FM", "AFM"], data[:, 1]*1000)
        ax.set(ylabel="Relative energy (meV/atom)")
    else:
        labels = {"metal": ("Linear hydrostatic strain", "Energy (eV/atom)"),
                  "inorganic": ("Volume ($\\AA^3$/atom)", "Energy (eV/atom)"),
                  "battery": ("x in Li$_x$C$_6$", "Formation energy (eV/C$_6$)")}
        ax.plot(data[:, 0], data[:, 1], "o-")
        ax.set(xlabel=labels[case][0], ylabel=labels[case][1])
    ax.set_title(case)
    ax.grid(alpha=.2)
    fig.savefig(output or work / "result.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, help="读取复制并修改后的 JSON 参数，不改动仓库模板")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--continue-md", action="store_true", help="从 STOPCAR 正常停止的 MD 段保留速度补足剩余步数；须同时 --resume")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--ranks", type=int, default=1)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--potential-root", type=Path, default=Path.home()/"Software/VASP/potentials/PBE")
    parser.add_argument("--lammps-potentials", type=Path, default=Path.home()/"Software/LAMMPS/30Sep2026/install/share/lammps/potentials")
    parser.add_argument("--vasp", default="vasp_std")
    parser.add_argument("--lammps", default="lmp")
    parser.add_argument("--orca", default="orca")
    parser.add_argument("--btp2", default="btp2")
    args = parser.parse_args()
    if args.ranks < 1 or args.threads < 1:
        parser.error("进程数、线程数须为正整数")
    if args.continue_md and not args.resume:
        parser.error("--continue-md 须与 --resume 一起使用")
    r = Runner(args)
    globals()[args.case.replace("-", "_")](r)


if __name__ == "__main__":
    main()
