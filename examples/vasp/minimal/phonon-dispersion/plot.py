"""用法：python3 plot.py；读取 Phonopy band.yaml，绘制声子色散。"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml


def arguments(default_output):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path(default_output))
    return parser.parse_args()


def save(fig, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"已生成 {output}")


def main():
    args = arguments("si-phonons.png")
    data = yaml.safe_load((args.input_dir / "band.yaml").read_text())
    points = data["phonon"]
    distances = np.array([point["distance"] for point in points])
    frequencies = np.array(
        [[mode["frequency"] for mode in point["band"]] for point in points]
    )
    if not np.isfinite(frequencies).all():
        raise SystemExit("声子数据含非有限值")
    ends = np.cumsum(data["segment_nqpoint"]) - 1
    ticks = [distances[0], *distances[ends]]
    labels = [data["labels"][0][0], *[pair[1] for pair in data["labels"]]]
    labels = [r"$\Gamma$" if label in ("G", "GAMMA") else label for label in labels]
    fig, ax = plt.subplots(figsize=(5.8, 4.3), constrained_layout=True)
    ax.plot(distances, frequencies, color="#24618c", linewidth=1.1)
    for tick in ticks:
        ax.axvline(tick, color="0.85", linewidth=0.7)
    ax.axhline(0, color="0.35", linewidth=0.8)
    ax.set(
        xlim=(ticks[0], ticks[-1]),
        ylim=(min(-0.5, frequencies.min() - 0.3), frequencies.max() + 0.7),
        ylabel="Frequency (THz)",
        title="Si | harmonic phonon dispersion",
    )
    ax.set_xticks(ticks, labels)
    save(fig, args.output)


if __name__ == "__main__":
    main()
