"""核对准分子密度孔洞、UFF模型势与人工变胞帧的空隙统计。

从仓库调用：python examples/multiwfn/cavity-and-potential/analyze.py \
    --work-root WORK --output-dir OUT --log-name multiwfn.out
仅用于本例理想C20几何、孤立Ar和单Ar正交周期帧，不是MD轨迹采样器。
"""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import numpy as np
from scipy.ndimage import label

# 当前脚本同名，显式载入既有 Cube 读取器，避免导入自身。
reader = Path(__file__).resolve().parents[2]/'orca/minimal/weak-interactions/analyze.py'
spec = importlib.util.spec_from_file_location('water_dimer_cube_reader', reader)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cube, BOHR_A = module.cube, module.BOHR_A


def central_domain(field, origin, vectors, cutoff):
    indices = np.rint(-origin @ np.linalg.inv(vectors)).astype(int)
    if np.any(indices < 0) or np.any(indices >= field.shape):
        raise ValueError('原点必须处于本例网格内')
    labels, count = label(field < cutoff, structure=np.ones((3, 3, 3)))
    idx = int(labels[tuple(indices)])
    mask = labels == idx if idx else np.zeros_like(field, dtype=bool)
    touching = bool(any(np.take(mask, side, axis=axis).any() for axis in range(3) for side in [0, -1]))
    volume = float(mask.sum()*abs(np.linalg.det(vectors))*BOHR_A**3) if idx else None
    return dict(cutoff_e_Bohr3=cutoff, total_domains=int(count), local_label=idx, center_node_density=float(field[tuple(indices)]),
                points=int(mask.sum()), touches_box=touching, volume_A3=volume if idx and not touching else None,
                clipped_component_volume_A3=volume, status='absent' if not idx else 'connected_to_box' if touching else 'closed_component'), mask


def pair_uff(distance, epsilon, rmin):
    distance = np.asarray(distance, dtype=float)
    if not np.isfinite(distance).all() or np.any(distance <= 0):
        raise ValueError('LJ距离必须为有限正值')
    x6 = (rmin/distance)**6
    rep = epsilon*x6*x6
    disp = -2*epsilon*x6
    return rep, disp, rep+disp


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work-root', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--log-name', default='multiwfn.out')
    args = ap.parse_args()
    root = args.work_root
    cavity = {}
    source_hashes = {}
    for name, directory in [('coarse', 'cage-density'), ('fine', 'cage-density-fine')]:
        path = root/directory/'density.cub'
        field, origin, vectors, atoms = cube(path)
        if len(atoms) != 20 or not np.all(atoms[:, 0] == 6):
            raise ValueError('本例需要20个理想笼状碳位点')
        if not np.allclose(np.linalg.norm(atoms[:, 2:]*BOHR_A, axis=1), 2.2, atol=2e-6):
            raise ValueError('本例碳位点外接球半径应为2.2Å')
        rows = [central_domain(field, origin, vectors, t)[0] for t in [.001, .005, .01, .02, .05]]
        cavity[name] = dict(shape=list(field.shape), origin_Bohr=origin.tolist(), vectors_Bohr=vectors.tolist(), thresholds=rows)
        for cutoff, native_dir in [( .01, 'domain-010' if name == 'coarse' else 'domain-fine')]+([(.05, 'domain-050')] if name == 'coarse' else []):
            result, mask = central_domain(field, origin, vectors, cutoff)
            exported, eo, ev, ea = cube(root/native_dir/'domain.cub')
            if field.shape != exported.shape or not np.allclose(origin, eo) or not np.allclose(vectors, ev) or not np.allclose(atoms, ea):
                raise ValueError('域导出网格与密度场不对应')
            expected = mask.copy()
            for axis in range(3):
                for side in [0, -1]:
                    sl = [slice(None)]*3; sl[axis] = side; expected[tuple(sl)] = False
            if not np.array_equal(exported, expected):
                raise ValueError('导出域不包含所需中心区域：不能跨程序假定域号一致')
            points = np.loadtxt(root/native_dir/'domain.txt')
            index = np.rint((points[:, :3]/BOHR_A-origin) @ np.linalg.inv(vectors)).astype(int)
            flat = np.ravel_multi_index(index.T, field.shape)
            if len(points) != mask.sum() or not np.array_equal(np.sort(flat), np.flatnonzero(mask)):
                raise ValueError('未封口的域坐标与中心连通域不一致')
            if not np.allclose(points[:, 3], field[tuple(index.T)], rtol=1e-8, atol=1e-12):
                raise ValueError('域坐标对应的密度值不一致')
        source_hashes[directory] = hashlib.sha256(path.read_bytes()).hexdigest()
        if name == 'coarse':
            z = int(np.argmin(abs(origin[2]+np.arange(field.shape[2])*vectors[2, 2])))
            section = dict(x_A=((origin[0]+np.arange(field.shape[0])*vectors[0, 0])*BOHR_A).tolist(),
                           y_A=((origin[1]+np.arange(field.shape[1])*vectors[1, 1])*BOHR_A).tolist(),
                           z_A=float((origin[2]+z*vectors[2, 2])*BOHR_A), density=field[:, :, z].tolist())
    rep, o, v, a = cube(root/'vdw/repul.cub')
    disp, od, vd, ad = cube(root/'vdw/disp.cub')
    total, ot, vt, at = cube(root/'vdw/vdW.cub')
    if len(a) != 1 or a[0, 0] != 18 or not all(np.allclose(x, y) for x, y in [(o, od), (o, ot), (v, vd), (v, vt), (a, ad), (a, at)]) or rep.shape != disp.shape or rep.shape != total.shape:
        raise ValueError('本例UFF三份网格应对应同一个孤立Ar原子')
    if not re.search(r'Element of probe atom:\s*C\s', (root/'vdw'/args.log_name).read_text()):
        raise ValueError('本例原生网格需要C探针；按实际日志检查默认值')
    coords = (o+np.indices(rep.shape).transpose(1, 2, 3, 0) @ v)*BOHR_A
    radius = np.linalg.norm(coords-a[0, 2:]*BOHR_A, axis=-1)
    eps, rmin = (.185*.105)**.5, (3.868*3.851)**.5
    reconstructed = pair_uff(radius, eps, rmin)
    errors = []
    for name in ['repul.cub', 'disp.cub', 'vdW.cub']:
        source_hashes['vdw/'+name] = hashlib.sha256((root/'vdw'/name).read_bytes()).hexdigest()
    # Cube头部坐标/步矢保留6位小数，r^-12在近核处会放大其舍入误差。
    index = np.indices(rep.shape).transpose(1, 2, 3, 0)
    coordinate_bound = np.linalg.norm((index+2)*(.5e-6*BOHR_A), axis=-1)
    scale = abs(reconstructed[0])+abs(reconstructed[1])
    rounding_bound = 6e-6*scale + 1.01*(12*abs(reconstructed[0])+6*abs(reconstructed[1]))*coordinate_bound/np.maximum(radius-coordinate_bound, 1e-12)
    for native, expected in zip([rep, disp, total], reconstructed):
        err = float(np.max(abs(native-expected)/np.maximum(abs(reconstructed[0])+abs(reconstructed[1]), 1e-12)))
        if np.any(abs(native-expected) > rounding_bound):
            raise ValueError('原生UFF网格与几何混合的12-6势不符')
        errors.append(err)
    rr = np.linspace(2.8, 8., 400)
    curves = {}
    for element, well, length in [('He', .056, 2.362), ('C', .105, 3.851), ('Ar', .185, 3.868)]:
        e, x = (.185*well)**.5, (3.868*length)**.5
        curves[element] = dict(epsilon_kcal_mol=e, minimum_radius_A=x, minimum_energy_kcal_mol=-e, values_kcal_mol=pair_uff(rr, e, x)[2].tolist())
    frames = []
    for directory, L, periodic in [('frame-075', 7.5, True), ('frame-080', 8., True), ('frame-085', 8.5, True), ('frame-nopbc', 8.5, False), ('frame-gauss', 8.5, True)]:
        raw, origin, vectors, atoms = cube(root/directory/'free_prim.cub')
        if len(atoms) != 1 or atoms[0, 0] != 18:
            raise ValueError('人工帧必须是单Ar模型')
        delta = (origin+np.indices(raw.shape).transpose(1, 2, 3, 0) @ vectors-atoms[0, 2:])*BOHR_A
        if periodic:
            delta -= np.rint(delta/L)*L
        mask = np.linalg.norm(delta, axis=-1) >= 1.88
        if not np.array_equal(raw, mask):
            raise ValueError('人工帧原始网格与相应周期边界不符')
        volume = float(mask[:-1, :-1, :-1].mean()*L**3)
        native = float(re.search(r'Free volume:\s*([\d.]+)', (root/directory/args.log_name).read_text())[1])
        if abs(volume-native) > .002:
            raise ValueError('人工帧积分与日志不符')
        frames.append(dict(directory=directory, box_A3=L**3, free_A3=volume, fraction=volume/L**3, periodic=periodic))
        for name in ['free_prim.cub', 'free_smooth.cub']:
            source_hashes[directory+'/'+name] = hashlib.sha256((root/directory/name).read_bytes()).hexdigest()
    erf = cube(root/'frame-085/free_smooth.cub')[0]
    gauss = cube(root/'frame-gauss/free_smooth.cub')[0]
    if np.array_equal(erf, gauss) or frames[2]['free_A3'] != frames[4]['free_A3']:
        raise ValueError('平滑切换应只改变显示场，原始积分应一致')
    equal_mean = float(np.mean([x['fraction'] for x in frames[:3]]))
    volume_weighted = float(sum(x['free_A3'] for x in frames[:3])/sum(x['box_A3'] for x in frames[:3]))
    result = dict(models='Ideal C20 dodecahedron, radius2.2A, no optimized wavefunction; isolated Ar with defaultC UFF probe; constructed single-Ar varying-cell frames, not an MD trajectory',
                  cavity=cavity, cavity_section=section, cavity_units='density e/Bohr^3; volume Angstrom^3; nonperiodic26-connectivity node counting',
                  uff=dict(host='Ar', native_probe='C', parameter_source='UFF well depth and x parameters, Multiwfn2026.7.15', host_epsilon_kcal_mol=.185, host_x_A=3.868,
                           native_grid_max_scaled_errors=errors, rounding_check='Cube6-decimal coordinate and6-significant-digit value bounds propagated through r^-12/r^-6', curve_radius_A=rr.tolist(), curves=curves,
                           alternative_probes='He and Ar curves independently calculated with the same formula; not additional Multiwfn probe runs'),
                  constructed_frames=frames, frame_integration='one corner per grid cell, final endpoint excluded; voxel uses exact CIF L^3 divided by cell count, avoiding rounded Cube-step drift', equal_frame_mean_fraction=equal_mean, ratio_of_mean_volumes=volume_weighted,
                  smoothing_changes_field_not_raw_volume=True, source_sha256=source_hashes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'cavity-potential.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(cavity_coarse=cavity['coarse']['thresholds'], uff_errors=errors, frame_means=[equal_mean, volume_weighted]), ensure_ascii=False))


if __name__ == '__main__':
    main()
