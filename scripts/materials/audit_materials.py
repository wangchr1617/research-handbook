"""检查材料案例的数据与文件摘要：python audit_materials.py [--verify-local] [--report FILE]。

数值数据从案例目录读取，运行诊断从本地 _validation_runs 读取。
--verify-local 另核对本地原始输入/输出摘要。缺失或无效证据返回非零状态。
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from run_case import CASES, ROOT
from record_startup import STARTUP_CASES, validate_receipt


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(verify_local=False):
    issues = []
    results = {}
    for case in CASES:
        target = ROOT / "examples/materials" / case
        data = target / "data"
        if case in STARTUP_CASES and not (data / "results.json").is_file():
            try:
                diagnostics = ROOT / "_validation_runs/materials" / case
                receipt = json.loads((diagnostics / "startup.json").read_text())
                validate_receipt(receipt)
                if receipt["case"] != case or receipt["config"] != json.loads(
                        (ROOT / "inputs/materials" / (case + ".json")).read_text()):
                    raise ValueError("启动参数与公开输入不符")
                if digest(diagnostics / "startup.log") != receipt["excerpt_sha256"]:
                    raise ValueError("日志摘录摘要不匹配")
                if verify_local:
                    for name, task in receipt["tasks"].items():
                        local = ROOT / "_validation_runs/materials" / case / name
                        for group in ("input_sha256", "output_sha256"):
                            for file, value in task[group].items():
                                if digest(local / file) != value:
                                    raise ValueError(f"{name}/{file} 本地摘要不匹配")
                results[case] = {"verification": "startup", "properties_complete": False,
                                 "tasks": len(receipt["tasks"]),
                                 "ionic_steps": {n: t["ionic_steps"] for n, t in receipt["tasks"].items()}}
            except (OSError, ValueError, KeyError, TypeError) as exc:
                issues.append(f"{case} 启动证据无效：{exc}")
            continue
        missing = [name for name in ("curve.csv", "result.png", "results.json", "provenance.json")
                   if not (data / name).is_file()]
        if missing:
            issues.append(f"{case} 缺少实际数据：{', '.join(missing)}")
            continue
        result = json.loads((data / "results.json").read_text())
        provenance = json.loads((data / "provenance.json").read_text())
        curve = np.loadtxt(data / "curve.csv", delimiter=",", skiprows=1, ndmin=2)
        if not np.isfinite(curve).all() or len(curve) < 2:
            issues.append(f"{case} 数值表非有限或点数不足")
        if provenance["config"] != json.loads((ROOT / "inputs/materials" / (case + ".json")).read_text()):
            issues.append(f"{case} 结果参数与公开输入不同")
        derived = provenance.get("derived_sha256", {})
        for name in ("curve.csv", "result.png", "results.json"):
            if derived.get(name) != digest(data / name):
                issues.append(f"{case}/{name} 缺少或不匹配提取数据摘要")
        if not provenance["tasks"]:
            issues.append(f"{case} 缺少计算任务记录")
        if verify_local:
            for name, task in provenance["tasks"].items():
                local = ROOT / "_validation_runs/materials" / case / name
                for group in ("input_sha256", "output_sha256"):
                    for file, value in task[group].items():
                        if not (local / file).is_file() or digest(local / file) != value:
                            issues.append(f"{case}/{name}/{file} 本地摘要不匹配")
        if case == "ferroelectric" and (result["energy_inversion_error_eV"] > 1e-5 or
                                       result["polarization_inversion_error_C_m2"] > 1e-3):
            issues.append("BaTiO3 路径反演关系异常")
        if case == "inorganic" and not (curve[:, 0].min() < result["equilibrium_volume_A3_atom"] < curve[:, 0].max()):
            issues.append("MgO 状态方程极小值不在采样区间")
        if case == "battery":
            e = result["energies_eV_cell"]
            delta = e["LiC6"] - 1.5*e["graphite"] - .5*e["Li-metal"]
            if not np.isclose(-delta, result["average_voltage_V_vs_Li"], atol=1e-10):
                issues.append("LiC6 反应配平或电压符号错误")
        if case == "electrocatalysis":
            if not np.allclose(curve[:, 2], result["delta_G_H_eV"] + curve[:, 0]) or not np.allclose(curve[:, 3], 2*curve[:, 0]):
                issues.append("HER 台阶图电位参考不一致")
            if len(result["frequencies_cm-1"]["H-ads"]) != 3:
                issues.append("H 局部 Hessian 振动数不符")
        if case == "phase-change":
            c = provenance["config"]
            if not np.isclose(result["time_fs"], c["dt_fs"]*sum(s["steps"] for s in c["stages"])):
                issues.append("GeTe 轨迹总时长不足")
            for name in ("rdf.csv", "msd.csv", "structure-results.json", "structure.png"):
                if not (data / name).is_file() or derived.get(name) != digest(data / name):
                    issues.append(f"GeTe 缺少或不匹配结构分析数据：{name}")
        results[case] = {"verification": "numerical", "rows": len(curve), "tasks": len(provenance["tasks"])}
    return {"required_cases": list(CASES), "available_cases": results, "issues": issues,
            "scope": "按数值数据或本地运行诊断的类型检查文件、参数与摘要",
            "numerical_cases": sum(r["verification"] == "numerical" for r in results.values()),
            "startup_cases": sum(r["verification"] == "startup" for r in results.values()),
            "complete": not issues and len(results) == len(CASES)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-local", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = audit(args.verify_local)
    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.write_text(content)
    print(content)
    raise SystemExit(0 if report["complete"] else 1)


if __name__ == "__main__":
    main()
