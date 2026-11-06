"""从 VASP 输出生成运行诊断摘要，不启动计算。

用法：python record_startup.py CASE --work DIR。
只接受电子步收敛且正常停止的真实 VASP 输出；原始输入和授权势只记录摘要。
诊断记录保存在本地运行目录，不导出到公开案例。
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from ase.io import read

from run_case import ROOT, controlled_md_stop, dump, sha, vasp_result

STARTUP_CASES = {"phase-change", "electrocatalysis"}


def validate_receipt(receipt):
    case = receipt["case"]
    if case not in STARTUP_CASES or receipt["kind"] != "startup" or receipt["properties_complete"] is not False:
        raise ValueError("启动证据的案例或验收范围不符")
    expected = (["melt"] + [f"melt-continue-{i:03d}" for i in range(1, len(receipt["tasks"]))]
                if case == "phase-change" else ["clean", "H-ads"])
    if not receipt["tasks"] or list(receipt["tasks"]) != expected:
        raise ValueError("启动证据缺少预期任务")
    for name, task in receipt["tasks"].items():
        if task["ionic_steps"] < 2 or not 0 < task["max_scf_steps"] < task["NELM"] or not task["normal_end"]:
            raise ValueError("没有足够的实际收敛迭代或正常结束证据")
        for group, required in (("input_sha256", {"INCAR", "POSCAR", "KPOINTS", "POTCAR"}),
                                ("output_sha256", {"OUTCAR", "vasprun.xml", "CONTCAR", "stdout.log"})):
            if not required <= task[group].keys() or any(not re.fullmatch(r"[0-9a-f]{64}", h) for h in task[group].values()):
                raise ValueError("启动证据缺少有效输入输出摘要")
        composition = ({"Ge": 16, "Te": 16} if case == "phase-change" else
                       {"Pt": 12} if name == "clean" else {"Pt": 12, "H": 1})
        if task["composition"] != composition:
            raise ValueError("实际模型组成不符")
        if name == "clean":
            if not task["ionic_converged"]:
                raise ValueError("Pt 洁净表面没有完成优化")
        elif not task["controlled_stop"] or task["ionic_steps"] >= task["requested_steps"]:
            raise ValueError("短任务缺少正常停止证据")
    if case == "phase-change":
        matches = receipt["restart_input_matches_previous_CONTCAR"]
        if len(matches) != len(expected)-1 or not all(matches):
            raise ValueError("MD 续算结构和速度没有原样衔接")


def record(case, work):
    work = work.resolve()
    if work.is_relative_to(ROOT) and not work.is_relative_to(ROOT / "_validation_runs"):
        raise ValueError("运行诊断须保存在 _validation_runs 或仓库外的运行目录")
    config = json.loads((ROOT / "inputs/materials" / (case + ".json")).read_text())
    original = json.loads((work / "provenance.json").read_text())
    if config != original["config"]:
        raise ValueError("实际运行参数与公开输入不同")
    names = (["melt"] + [p.name for p in sorted(work.glob("melt-continue-*")) if p.is_dir()]
             if case == "phase-change" else ["clean", "H-ads"])
    receipt = {"schema_version": 1, "case": case, "kind": "startup",
               "properties_complete": False, "config": config, "tasks": {}}
    excerpts = []
    for name in names:
        local = work / name
        result, _, _ = vasp_result(local)
        tree = ET.parse(local / "vasprun.xml").getroot()
        settings = tree.find("parameters")
        def parameter(key):
            return int(settings.find(f".//i[@name='{key}']").text)
        log = (local / "stdout.log").read_text(errors="replace")
        result.update(NELM=parameter("NELM"), requested_steps=parameter("NSW"),
                      normal_end=True, controlled_stop=controlled_md_stop(local),
                      composition=dict(Counter(read(local / "POSCAR").get_chemical_symbols())),
                      executable="vasp_gam" if "gamma-only" in log else "vasp_std")
        for group, files in (("input_sha256", ("INCAR", "POSCAR", "KPOINTS", "POTCAR")),
                             ("output_sha256", ("OUTCAR", "vasprun.xml", "CONTCAR", "stdout.log", "REPORT"))):
            result[group] = {f: sha(local / f) for f in files if (local / f).is_file()}
        receipt["tasks"][name] = result
        excerpts.append(f"[{case}/{name}]")
        # 只保留程序版本、离子步及停止标记，避免发布完整授权输出。
        excerpts.extend(line.strip() for line in log.splitlines() if
                        re.match(r"\s*(vasp\.\d|\d+\s+(?:T=|F=)|soft stop encountered!|deleting file STOPCAR)", line))
        excerpts.append("OUTCAR: General timing and accounting (normal end)\n")
    if case == "phase-change":
        receipt["restart_input_matches_previous_CONTCAR"] = [
            (work / before / "CONTCAR").read_bytes() == (work / after / "POSCAR").read_bytes()
            for before, after in zip(names, names[1:])]
        receipt["verified_MD_steps"] = sum(t["ionic_steps"] for t in receipt["tasks"].values())
        receipt["verified_MD_time_fs"] = receipt["verified_MD_steps"] * config["dt_fs"]
        receipt["unverified"] = ["完整熔融阶段", "淬火与退火", "非晶形成与晶化", "完整轨迹结构统计"]
    else:
        receipt["unverified"] = ["吸附结构优化收敛", "H2参考与振动频率", "吸氢自由能", "HER自由能台阶图"]
    validate_receipt(receipt)
    (work / "startup.log").write_text("\n".join(excerpts) + "\n")
    receipt["excerpt_sha256"] = sha(work / "startup.log")
    dump(work / "startup.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=sorted(STARTUP_CASES))
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    receipt = record(args.case, args.work)
    print(json.dumps({"case": args.case, "kind": receipt["kind"], "tasks": {
        n: t["ionic_steps"] for n, t in receipt["tasks"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
