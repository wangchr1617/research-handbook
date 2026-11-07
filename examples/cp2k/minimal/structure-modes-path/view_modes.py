"""读取 CP2K 振动 Molden，导出人为振幅的 XYZ 模式动画与数值摘要。

用法：python view_modes.py --input water-vibrations.mol --output-dir OUT --amplitude 0.15
FR-COORD 为 Bohr；amplitude 是显示时最大原子位移，单位 Å，不是热振幅。
"""

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np

BOHR_A = 0.529177210903


def read_molden(file):
    sections, current = {}, None
    for line in Path(file).read_text().splitlines():
        match = re.match(r"\s*\[([^]]+)\](.*)", line)
        if match:
            current = match[1].upper()
            if current in sections:
                raise ValueError(f"重复的 Molden 字段 {current}")
            sections[current] = dict(suffix=match[2].strip(), lines=[])
        elif line.strip() and current is not None:
            sections[current]["lines"].append(line.strip())
    for field in ["MOLDEN FORMAT", "FREQ", "FR-COORD", "FR-NORM-COORD"]:
        if field not in sections:
            raise ValueError(f"缺少振动字段 {field}，不能仅按 .mol 后缀判断格式")
    xyz_rows = [row.split() for row in sections["FR-COORD"]["lines"]]
    elements = [row[0] for row in xyz_rows]
    xyz = np.array([[float(x) for x in row[1:]] for row in xyz_rows])
    frequencies = np.array([float(x) for x in sections["FREQ"]["lines"]])
    vectors, ids, block = [], [], []
    for line in sections["FR-NORM-COORD"]["lines"]:
        if line.lower().startswith("vibration"):
            if block:
                vectors.append(block)
                block = []
            ids.append(int(line.split()[1]))
        else:
            block.append([float(x) for x in line.split()])
    if block:
        vectors.append(block)
    vectors = np.array(vectors)
    if xyz.shape != (len(elements), 3) or vectors.shape != (len(frequencies), len(elements), 3):
        raise ValueError("频率、模式数、原子数或位移列数不匹配")
    if ids != list(range(1, len(frequencies) + 1)):
        raise ValueError("模式编号应与本文件的频率表逐项对应")
    if not all(np.isfinite(a).all() for a in [xyz, frequencies, vectors]):
        raise ValueError("振动数据含非有限值")
    intensities = None
    if "INT" in sections:
        intensities = np.array([[float(x) for x in row.split()] for row in sections["INT"]["lines"]])
        if len(intensities) != len(frequencies) or not np.isfinite(intensities).all():
            raise ValueError("强度表与频率表不相容")
    if "ATOMS" in sections:
        rows = [row.split() for row in sections["ATOMS"]["lines"]]
        atom_xyz = np.array([[float(x) for x in row[3:]] for row in rows])
        unit = sections["ATOMS"]["suffix"].upper()
        if unit == "ANGS":
            atom_xyz /= BOHR_A
        elif unit != "AU":
            raise ValueError("未知的 Atoms 坐标单位")
        if [row[0] for row in rows] != elements or not np.allclose(atom_xyz, xyz, atol=1e-6, rtol=0):
            raise ValueError("Atoms 与 FR-COORD 的元素、顺序或坐标不一致")
    return elements, xyz * BOHR_A, frequencies, vectors, intensities


def trajectory(elements, xyz, vector, amplitude, frames):
    maximum = np.linalg.norm(vector, axis=1).max()
    if maximum == 0 or amplitude <= 0 or not math.isfinite(amplitude) or frames < 4:
        raise ValueError("需要非零模式、正的有限显示振幅和至少4帧")
    displacement = vector / maximum * amplitude
    coordinates = xyz + np.sin(np.arange(frames) * 2 * np.pi / frames)[:, None, None] * displacement
    return displacement, coordinates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--amplitude", type=float, default=0.15)
    parser.add_argument("--frames", type=int, default=24)
    args = parser.parse_args()
    elements, xyz, frequencies, modes, intensities = read_molden(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_displacements = []
    for n, (freq, vector) in enumerate(zip(frequencies, modes), 1):
        displacement, coordinates = trajectory(elements, xyz, vector, args.amplitude, args.frames)
        all_displacements.append(displacement)
        text = []
        for frame, positions in enumerate(coordinates):
            text.extend([f"{len(elements)}\n", f"Mode {n}, {freq:.6f} cm^-1; display frame {frame}; artificial amplitude {args.amplitude} Angstrom\n"])
            text.extend(f"{element} {pos[0]:.10f} {pos[1]:.10f} {pos[2]:.10f}\n" for element, pos in zip(elements, positions))
        (args.output_dir / f"mode-{n:03d}.xyz").write_text("".join(text))
    report = dict(elements=elements, coordinates_angstrom=xyz.tolist(), frequencies_cm_minus1=frequencies.tolist(),
                  normal_vectors=modes.tolist(), display_displacements_angstrom=np.array(all_displacements).tolist(),
                  display_max_atom_amplitude_angstrom=args.amplitude, frames=args.frames,
                  intensity_present=intensities is not None,
                  intensities=None if intensities is None else intensities.tolist(),
                  meaning="Cartesian mode directions exported by CP2K; visualization normalization only, not thermal amplitude or physical time trajectory")
    (args.output_dir / "vibration-modes.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"读取 {len(elements)} 原子、{len(frequencies)} 模式；强度表：{intensities is not None}")


if __name__ == "__main__":
    main()
