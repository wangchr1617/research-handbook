"""分析已完成的 GeTe 三阶段轨迹：python analyze_phase.py RUN_DIR [--publish]。

提取分元素配位、部分 RDF 与去除质心漂移的 MSD；不启动计算或接受未完成阶段。
RDF 限于最短晶面间距的一半，避免小周期盒导致的重复计数。
"""

import argparse
import json
import os
from pathlib import Path

import numpy as np
from ase.build import bulk
from ase.io import write

from run_case import ROOT, dump, sha, vasp_result


def safe_radius(cell):
    cell = np.asarray(cell)
    volume = abs(np.linalg.det(cell))
    heights = [volume / np.linalg.norm(np.cross(cell[(i+1) % 3], cell[(i+2) % 3]))
               for i in range(3)]
    if not np.isfinite(heights).all() or min(heights) <= 0:
        raise ValueError("晶胞几何无效")
    return min(heights) / 2


def partial_rdf(frames, edges, species=("Ge", "Te")):
    pairs = [(species[0], species[0]), (species[0], species[1]), (species[1], species[1])]
    result = np.zeros((len(edges)-1, len(pairs)))
    shell = 4*np.pi/3 * np.diff(edges**3)
    for atoms in frames:
        if edges[-1] > safe_radius(atoms.cell) + 1e-10:
            raise ValueError("RDF 半径超过周期盒允许范围")
        symbols = np.array(atoms.get_chemical_symbols())
        distances = atoms.get_all_distances(mic=True)
        for col, (a, b) in enumerate(pairs):
            first, second = np.where(symbols == a)[0], np.where(symbols == b)[0]
            denominator = len(first)*(len(second)-(a == b))
            if denominator == 0:
                raise ValueError("原子数不足以定义部分 RDF")
            selected = distances[np.ix_(first, second)].copy()
            if a == b:
                np.fill_diagonal(selected, np.inf)
            histogram = np.histogram(selected, bins=edges)[0]
            # 同元素用有序原子对计数，归一化时排除自配对的有限 N 项。
            result[:, col] += histogram * atoms.get_volume() / (denominator*shell)
    return result / len(frames)


def coordination(frames, cutoff):
    if cutoff <= 0:
        raise ValueError("配位 cutoff 须大于零")
    samples = {"Ge": [], "Te": []}
    for atoms in frames:
        if cutoff >= safe_radius(atoms.cell):
            raise ValueError("配位 cutoff 接近或超过安全半径，需更大盒子")
        distances = atoms.get_all_distances(mic=True)
        np.fill_diagonal(distances, np.inf)
        counts = (distances < cutoff).sum(axis=1)
        for element in samples:
            mask = np.array(atoms.get_chemical_symbols()) == element
            samples[element].extend(counts[mask].tolist())
    return {element: {"mean": float(np.mean(values)), "std": float(np.std(values)),
                      "observations": len(values),
                      "histogram": {str(k): values.count(k) for k in sorted(set(values))}}
            for element, values in samples.items()}


def drift_corrected_msd(frames):
    if not frames:
        raise ValueError("没有轨迹帧")
    cell = frames[0].cell.array
    if any(not np.allclose(a.cell, cell, atol=1e-8) for a in frames):
        raise ValueError("此 MSD 实现仅适用于固定晶胞")
    symbols = np.array(frames[0].get_chemical_symbols())
    if any(a.get_chemical_symbols() != frames[0].get_chemical_symbols() for a in frames):
        raise ValueError("轨迹的原子顺序变化")
    fractional = np.array([a.get_scaled_positions(wrap=True) for a in frames])
    delta = np.diff(fractional, axis=0)
    delta -= np.rint(delta)
    unwrapped = np.concatenate([fractional[:1], fractional[:1] + np.cumsum(delta, axis=0)])
    displacement = (unwrapped - unwrapped[0]) @ cell
    weights = frames[0].get_masses()
    center_of_mass = np.average(displacement, axis=1, weights=weights)
    displacement -= center_of_mass[:, None, :]
    return np.column_stack([np.mean(np.sum(displacement[:, symbols == element]**2, axis=2), axis=1)
                            for element in ("Ge", "Te")])


def plot_statistics(work, stage_names):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rdf = np.loadtxt(work / "rdf.csv", delimiter=",", skiprows=1)
    msd = np.loadtxt(work / "msd.csv", delimiter=",", skiprows=1)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    colors = ["0.4", "#0072B2", "#D55E00", "#009E73"]
    for index, name in enumerate(["crystal-reference", *stage_names]):
        axes[0].plot(rdf[:, 0], rdf[:, 2+index*3], label=name, color=colors[index])
    axes[0].set(xlabel="Distance ($\\AA$)", ylabel="Ge-Te partial RDF", title="Safe-radius structure comparison")
    axes[0].legend(fontsize=8)
    for index, element in enumerate(["Ge", "Te"]):
        axes[1].plot(msd[:, 0]/1000, msd[:, index+1], label=element, color=colors[index+1])
    axes[1].set(xlabel="Time since first saved frame (ps)", ylabel="COM-corrected MSD ($\\AA^2$)",
                title="Nonstationary trajectory; no diffusion fit")
    axes[1].legend()
    for ax in axes:
        ax.grid(alpha=.2)
    fig.savefig(work / "structure.png", dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    work = args.run.resolve()
    os.environ["MPLCONFIGDIR"] = str(work / "mpl-cache")
    os.environ["XDG_CACHE_HOME"] = str(work / "cache")
    record = json.loads((work / "provenance.json").read_text())
    config = record["config"]
    if config["case"] != "phase-change":
        raise ValueError("该分析仅对应 GeTe 相变案例")
    trajectories = []
    result = json.loads((work / "results.json").read_text())
    segment_map = result.get("phase_segments", {})
    previous_segment = None
    for stage in config["stages"]:
        frames = []
        segments = segment_map.get(stage["name"], [{"task": stage["name"], "steps": stage["steps"]}])
        for segment in segments:
            directory = work / segment["task"]
            _, current, _ = vasp_result(directory)
            if len(current) != segment["steps"]:
                raise ValueError(f"{segment['task']} 步数与分段记录不符")
            task = record["tasks"][segment["task"]]
            for group in ("input_sha256", "output_sha256"):
                for name, value in task[group].items():
                    if sha(directory / name) != value:
                        raise ValueError("实际输入/输出与已完成任务摘要不符")
            if previous_segment and (directory / "POSCAR").read_bytes() != (previous_segment / "CONTCAR").read_bytes():
                raise ValueError("阶段间或续算段的结构、速度未原样衔接")
            previous_segment = directory
            frames.extend(current)
        if len(frames) != stage["steps"]:
            raise ValueError(f"{stage['name']} 分段总步数不完整")
        trajectories.append(frames)
    reference = bulk("GeTe", "rocksalt", a=config["a_A"]).repeat(config["repeat"])
    radius = min(safe_radius(a.cell) for group in trajectories for a in group)
    edges = np.linspace(0, radius*(1-1e-8), 101)
    groups = [[reference], *[frames[-50:] for frames in trajectories]]
    labels = ["crystal-reference", *[s["name"] for s in config["stages"]]]
    data = np.column_stack([(edges[:-1]+edges[1:])/2, *[partial_rdf(group, edges) for group in groups]])
    headers = ["r_A", *[f"{label}_{pair}" for label in labels for pair in ("GeGe", "GeTe", "TeTe")]]
    np.savetxt(work / "rdf.csv", data, delimiter=",", header=",".join(headers), comments="")
    all_frames = [a for group in trajectories for a in group]
    msd = drift_corrected_msd(all_frames)
    np.savetxt(work / "msd.csv", np.column_stack([np.arange(len(all_frames))*config["dt_fs"], msd]),
               delimiter=",", header="time_since_first_frame_fs,Ge_MSD_A2,Te_MSD_A2", comments="")
    statistics = {label: coordination(group, config["coordination_cutoff_A"])
                  for label, group in zip(labels, groups)}
    dump(work / "structure-results.json", {"safe_radius_A": radius, "rdf_bins": 100,
         "sampled_frames": dict(zip(labels, map(len, groups))), "coordination_cutoff_A": config["coordination_cutoff_A"],
         "coordination": statistics,
         "normalization": "ordered pairs; finite-N self exclusion for same species; stage-end arithmetic frame average",
         "MSD": "unwrapped fixed-cell positions with mass-weighted total COM drift removed; first frame is time zero; no diffusion fit"})
    write(work / "trajectory.extxyz", all_frames)
    plot_statistics(work, labels[1:])
    record["phase_structure_analysis_sha256"] = sha(Path(__file__))
    files = ("rdf.csv", "msd.csv", "structure-results.json", "structure.png")
    record.setdefault("derived_sha256", {}).update({name: sha(work/name) for name in files})
    dump(work / "provenance.json", record)
    if args.publish:
        destination = ROOT / "examples/materials/phase-change/data"
        destination.mkdir(exist_ok=True, parents=True)
        for name in (*files, "provenance.json"):
            (destination/name).write_bytes((work/name).read_bytes())
    print(json.dumps({"frames": len(all_frames), "safe_radius_A": radius, "coordination": statistics}, indent=2))


if __name__ == "__main__":
    main()
