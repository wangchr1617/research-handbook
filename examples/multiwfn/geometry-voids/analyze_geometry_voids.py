"""核对自建几何模型与 Multiwfn 原始/平滑自由区域网格。

在仓库中调用：python examples/multiwfn/geometry-voids/analyze_geometry_voids.py \
    --work-root WORK --output-dir OUT
只支持本例正交8Å立方晶胞、单Ar原子和P1水的结构教学模型。
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

# 复用仓库已有的正交、单标量 Cube 读取器；从仓库调用，无需复制脚本。
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'orca/minimal/weak-interactions'))
from analyze import BOHR_A, cube


def xyz(path):
    lines = path.read_text().splitlines()
    n = int(lines[0])
    rows = [line.split() for line in lines[2:2+n]]
    if len(rows) != n:
        raise ValueError('XYZ原子数不符')
    return [r[0] for r in rows], np.array([r[1:4] for r in rows], dtype=float)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work-root', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--log-name', default='multiwfn.out')
    args = ap.parse_args()
    r = args.work_root
    elements, original = xyz(r/'rotate/structure.xyz')
    elements2, rotated = xyz(r/'rotate/rotated.xyz')
    R = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], dtype=float)
    expected = original @ R.T
    expected -= expected[:3].mean(axis=0)
    error = float(np.max(abs(expected-rotated)))
    if elements != elements2 or error > 1e-7:
        raise ValueError('旋转/居中与独立矩阵变换不符')
    elw, whole = xyz(r/'cluster/whole.xyz')
    elc, cluster = xyz(r/'cluster/cluster.xyz')
    if elw != ['O', 'H', 'H'] or len(elc) % 3 or elc != ['O', 'H', 'H']*(len(elc)//3):
        raise ValueError('水分子的原子顺序或完整性不符')
    bonds = np.linalg.norm(whole[1:]-whole[0], axis=1)
    for block in cluster.reshape(-1, 3, 3):
        if not np.allclose(block-block[0], whole-whole[0], atol=1e-7):
            raise ValueError('提取团簇出现分子内部几何变化')
    translations = cluster.reshape(-1, 3, 3)[:, 0]-whole[0]
    if not np.allclose(translations/4, np.rint(translations/4), atol=1e-7):
        raise ValueError('邻近分子不是4Å晶格的平移镜像')
    free_rows, arrays, hashes = [], {}, {}
    radius = 1.88
    for name, requested, scale in [('free-050', .5, 1.), ('free-025', .25, 1.), ('free-scale', .25, 1.2), ('free-cap', .25, 1.)]:
        raw, o, v, atoms = cube(r/name/'free_prim.cub')
        smooth, so, sv, sat = cube(r/name/'free_smooth.cub')
        if raw.shape != smooth.shape or not np.allclose(o, so) or not np.allclose(v, sv) or not np.allclose(atoms, sat):
            raise ValueError('原始和平滑网格不对应')
        if len(atoms) != 1 or atoms[0, 0] != 18:
            raise ValueError('本例只支持单Ar周期模型')
        step = np.diag(v)*BOHR_A
        extent = step*(np.array(raw.shape)-1)
        if not np.allclose(extent, 8., atol=3e-5) or not np.allclose(o, 0):
            raise ValueError('本例需要原点0、8Å立方晶胞')
        points = o + np.indices(raw.shape).transpose(1, 2, 3, 0) @ v
        displacement = points*BOHR_A-atoms[0, 2:]*BOHR_A
        displacement -= np.rint(displacement/8)*8
        distance = np.linalg.norm(displacement, axis=-1)
        expected_raw = (distance >= radius*scale).astype(float)
        if name == 'free-cap':
            for axis in range(3):
                for side in [0, -1]:
                    sl = [slice(None)]*3
                    sl[axis] = side
                    expected_raw[tuple(sl)] = 0
        if not np.array_equal(raw, expected_raw) or not np.all((smooth >= 0) & (smooth <= 1)):
            raise ValueError('原始自由区域与周期半径球重建不符')
        # 屏幕在边界封口前积分；原始统计使用不重复的(nx-1)*(ny-1)*(nz-1)单元。
        raw_uncapped = distance >= radius*scale
        voxel = abs(float(np.linalg.det(v)))*BOHR_A**3
        numerical = float(raw_uncapped[:-1, :-1, :-1].sum()*voxel)
        text = (r/name/args.log_name).read_text()
        native = float(re.search(r'Free volume:\s*([\d.]+)', text)[1])
        if abs(native-numerical) > .001:
            raise ValueError('独立体积分与屏幕输出不符')
        exact = 8**3-4*np.pi*(radius*scale)**3/3
        free_rows.append(dict(name=name, requested_spacing_A=requested, actual_vectors_A=(v*BOHR_A).tolist(), shape=list(raw.shape),
                              radius_A=radius, radius_scale=scale, raw_free_volume_A3=numerical, native_free_volume_A3=native,
                              analytic_sphere_free_volume_A3=exact, absolute_error_A3=abs(numerical-exact),
                              exported_raw_corner_sum_A3=float(raw[:-1, :-1, :-1].sum()*voxel),
                              visualization_boundary_capped=name == 'free-cap',
                              smoothed_threshold_volumes_A3={str(t): float((smooth[:-1, :-1, :-1] >= t).sum()*voxel) for t in [.2, .5, .8]}))
        arrays[name] = smooth
        hashes[name] = {f: hashlib.sha256((r/name/f).read_bytes()).hexdigest() for f in ['free_prim.cub', 'free_smooth.cub']}
        if name == 'free-025':
            z = int(np.argmin(abs(np.arange(raw.shape[2])*step[2]-4)))
            section = dict(x_A=(np.arange(raw.shape[0])*step[0]).tolist(), y_A=(np.arange(raw.shape[1])*step[1]).tolist(), z_A=float(z*step[2]), smooth=smooth[:, :, z].tolist())
    if not np.array_equal(arrays['free-025'], arrays['free-scale']):
        raise ValueError('本版半径缩放意外改变了平滑场，应核对实现')
    data = dict(model='Geometry-only teaching lattices, not optimized phases: one Ar in8Å cubic P1 cell; one wrapped water in4Å cell; fixed water dimer for rigid rotation',
                units='Coordinates Angstrom; volumes Angstrom^3; smoothing field dimensionless',
                rotation=dict(matrix=R.tolist(), first_water_geometric_center_target=[0, 0, 0], maximum_coordinate_error_A=error, original=original.tolist(), transformed=rotated.tolist()),
                cluster=dict(cell_A=(np.eye(3)*4).tolist(), contact_factor=1.2, whole_elements=elw, whole_A=whole.tolist(), cluster_elements=elc, cluster_A=cluster.tolist(), molecule_count=len(elc)//3, central_atoms=[1, 2, 3], OH_lengths_A=bonds.tolist(), translations_A=translations.tolist()),
                free_regions=free_rows, section=section,
                probe_center_example=dict(probe_radius_A=1., exclusion_radius_A=radius+1, analytic_allowed_center_volume_A3=8**3-4*np.pi*(radius+1)**3/3, definition='Geometrically allowed probe centers only; no pore-network accessibility analysis performed'),
                smooth_radius_scale_invariant=True, source_cube_sha256=hashes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'geometry-voids.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(rotation_error=error, water_molecules=len(elc)//3, free_volumes=[x['raw_free_volume_A3'] for x in free_rows], analytic_free_volume=free_rows[1]['analytic_sphere_free_volume_A3']), ensure_ascii=False))


if __name__ == '__main__':
    main()
