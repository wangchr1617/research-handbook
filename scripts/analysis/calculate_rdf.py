"""用 MDAnalysis 计算两组原子的径向分布（距离 Å，依赖 MDAnalysis、NumPy）。

用法：python calculate_rdf.py topology.tpr trajectory.xtc --select-a 'name OW' --select-b 'name OW'
      python calculate_rdf.py topology.tpr trajectory.xtc --select-a 'prop z > 30 and prop z < 36' --norm none --updating
全盒均匀体系可用 rdf 归一化；局部空间选区请用 none 输出每帧壳层计数，另建几何归一化。
相同组通过 exclusion_block=(1,1) 去除自配对，不再强行把第一个 bin 写成零。
"""

import argparse
import math
from pathlib import Path


def calculate(
    universe,
    select_a="all",
    select_b=None,
    rmax=20.0,
    nbins=200,
    norm="rdf",
    updating=False,
    start=None,
    stop=None,
    step=1,
    rdf_factory=None,
):
    import numpy as np

    if not math.isfinite(rmax) or rmax <= 0 or nbins <= 0 or step <= 0:
        raise ValueError("rmax、nbins 和 step 必须为正")
    if norm not in {"rdf", "none", "density"}:
        raise ValueError("归一化类型无效")
    if (start is not None and start < 0) or (stop is not None and stop <= (start or 0)):
        raise ValueError("帧范围须满足 0 <= start < stop")
    if updating and norm != "none":
        raise ValueError("动态选区只支持原始计数 norm=none，不能沿用全盒均匀密度归一化")
    if updating and select_b is not None and select_b != select_a:
        raise ValueError("动态选区须使用同一选择表达式，以保持自配对排除规则一致")
    a = universe.select_atoms(select_a, updating=updating)
    b = universe.select_atoms(select_b or select_a, updating=updating)
    if not len(a) or not len(b):
        raise ValueError("初始选区为空，请检查选择表达式与轨迹")
    identical = np.array_equal(a.indices, b.indices)
    if not identical and np.intersect1d(a.indices, b.indices).size:
        raise ValueError("两个选区部分重叠；请使用相同组或不相交组，以明确排除自配对")
    if rdf_factory is None:
        from MDAnalysis.analysis.rdf import InterRDF

        rdf_factory = InterRDF
    rdf = rdf_factory(
        a,
        b,
        range=(0.0, rmax),
        nbins=nbins,
        norm=norm,
        exclusion_block=(1, 1) if identical else None,
    )
    rdf.run(start=start, stop=stop, step=step)
    values = np.column_stack((rdf.results.bins, rdf.results.rdf))
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("RDF 结果为空或非有限，请检查盒子、选区及帧范围")
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topology", type=Path)
    parser.add_argument("trajectory", type=Path)
    parser.add_argument("--select-a", default="all")
    parser.add_argument("--select-b")
    parser.add_argument("--rmax", type=float, default=20.0)
    parser.add_argument("--nbins", type=int, default=200)
    parser.add_argument("--norm", choices=["rdf", "density", "none"], default="rdf")
    parser.add_argument("--updating", action="store_true")
    parser.add_argument("--start", type=int)
    parser.add_argument("--stop", type=int)
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("-o", "--output", type=Path, default=Path("rdf.txt"))
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("输出已存在")
    if not args.topology.is_file() or not args.trajectory.is_file():
        parser.error("拓扑或轨迹文件不存在")
    import MDAnalysis as mda
    import numpy as np

    try:
        values = calculate(
            mda.Universe(str(args.topology), str(args.trajectory)),
            args.select_a,
            args.select_b,
            args.rmax,
            args.nbins,
            args.norm,
            args.updating,
            args.start,
            args.stop,
            args.step,
        )
        with args.output.open("x") as stream:
            np.savetxt(
                stream,
                values,
                header=f"r_A value; norm={args.norm}; self_pairs_excluded",
            )
    except (OSError, ValueError, RuntimeError, IndexError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(f"已保存 {len(values)} 个 bin：{args.output}")


if __name__ == "__main__":
    main()
