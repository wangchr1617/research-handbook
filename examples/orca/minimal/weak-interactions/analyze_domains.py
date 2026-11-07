"""从配对 Cube 提取 IRI 域积分、轨道等值面与 HS 指纹的小型数据。

python analyze_domains.py --coarse-root WORK11 --fine-root WORK13 \
    --orbital-dir ORBITAL --hs-dir HS --output-dir .
WORK11 含 iri、density-gradient；WORK13 含 iri-010、fields-010。
IRI=1、指数1.1，四个密度分箱边界为 -0.05/-0.013/+0.009 a.u.。
域按非周期26邻接定义；体积分用格点计数，不代替边界插值积分。
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from scipy.ndimage import label

from analyze import BOHR_A, cube
from measure_surfaces import mesh_metrics


def matched(paths):
    loaded = [cube(p) for p in paths]
    ref = loaded[0]
    for x in loaded[1:]:
        if x[0].shape != ref[0].shape or any(not np.allclose(a, b, rtol=0, atol=1e-9) for a, b in zip(x[1:], ref[1:])):
            raise ValueError('域积分需要原子、原点、步矢与形状相同的网格')
    return loaded


def domains(iri, rho, signed, origin, vectors, level=1.0):
    if not all(np.isfinite(x).all() for x in [iri, rho, signed]) or np.any(rho < 0):
        raise ValueError('本例域积分需要有限的非负电子密度')
    if not np.allclose(abs(signed), rho, rtol=2e-5, atol=1e-10):
        raise ValueError('着色密度与被积分密度不匹配')
    mask = iri < level
    # 使用固定的 x 最快扫描顺序编号；程序间域号可能不同，按空间位置对应。
    lab, count = label(mask.transpose(2, 1, 0), structure=np.ones((3, 3, 3)))
    lab = lab.transpose(2, 1, 0)
    dv = abs(float(np.linalg.det(vectors)))
    bins = np.searchsorted([-.05, -.013, .009], signed, side='right')
    records = []
    for idx in range(1, count + 1):
        use = lab == idx
        points = np.argwhere(use)
        n = np.bincount(bins[use], minlength=4)
        q = np.bincount(bins[use], weights=rho[use], minlength=4) * dv
        v = n * dv
        qtot, vtot = float(q.sum()), float(v.sum())
        qatt, vatt = float(q[:3].sum()), float(v[:3].sum())
        records.append(dict(
            id=idx, points=int(use.sum()), centroid_A=((origin + points.mean(axis=0) @ vectors)*BOHR_A).tolist(),
            touches_box=bool(np.any(points.min(axis=0) == 0) or np.any(points.max(axis=0) == np.array(mask.shape)-1)),
            q_e=q.tolist(), volume_Bohr3=v.tolist(), volume_A3=(v*BOHR_A**3).tolist(),
            q_total_e=qtot, volume_total_A3=vtot*BOHR_A**3,
            mean_density_e_Bohr3=qtot/vtot,
            attraction_q_fraction=qatt/qtot if qtot else None,
            attraction_volume_fraction=vatt/vtot,
            attraction_mean_density_e_Bohr3=qatt/vatt if vatt else None,
            repulsion_mean_density_e_Bohr3=float(q[3]/v[3]) if v[3] else None,
            signed_density_range=[float(signed[use].min()), float(signed[use].max())],
        ))
    return records


def surface_log(path):
    s = path.read_text()
    v = re.search(r'\n\s*Volume:\s*[\d.]+\s*Bohr\^3\s*\(\s*([\d.]+)', s)
    a = re.search(r'Overall surface area:\s*[\d.]+\s*Bohr\^2\s*\(\s*([\d.]+)', s)
    if not v or not a:
        raise ValueError('日志缺少测量结果')
    return dict(volume_A3=float(v[1]), area_A2=float(a[1]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ['coarse-root', 'fine-root', 'orbital-dir', 'hs-dir', 'output-dir']:
        ap.add_argument('--'+k, type=Path, required=True)
    ap.add_argument('--log-name', default='multiwfn.out', help='轨道和HS目录中的日志文件名')
    args = ap.parse_args()
    hashes, summary = {}, {}
    model_atoms = None
    for name, paths in [
        ('coarse', [args.coarse_root/'iri/func2.cub', args.coarse_root/'density-gradient/func1.cub', args.coarse_root/'iri/func1.cub']),
        ('fine', [args.fine_root/'iri-010/func2.cub', args.fine_root/'fields-010/func1.cub', args.fine_root/'fields-010/func2.cub']),
    ]:
        data = matched(paths)
        if model_atoms is None:
            model_atoms = data[0][3]
        elif not np.allclose(model_atoms, data[0][3], rtol=0, atol=1e-9):
            raise ValueError('粗细网格对应的原子模型不同')
        fields = [x[0] for x in data]
        _, origin, vectors, _ = data[0]
        summary[name] = dict(shape=list(fields[0].shape), origin_Bohr=origin.tolist(), vectors_Bohr=vectors.tolist(), domains=domains(*fields, origin, vectors))
        for i, path in enumerate(paths):
            hashes[f'{name}-{i}'] = hashlib.sha256(path.read_bytes()).hexdigest()
    amp, origin, vectors, orbital_atoms = cube(args.orbital_dir/'MOvalue.cub')
    absolute, o2, v2, a2 = cube(args.orbital_dir/'surf.cub')
    if amp.shape != absolute.shape or not np.allclose(origin, o2) or not np.allclose(vectors, v2) or not np.allclose(orbital_atoms, a2) or not np.allclose(orbital_atoms, model_atoms) or not np.allclose(abs(amp), absolute, rtol=1e-5, atol=1e-9):
        raise ValueError('轨道绝对值与原始轨道网格不一致')
    orbital = [mesh_metrics(abs(amp), origin, vectors, level) for level in [.025, .05, .10]]
    if not all(x['closed'] and x['consistently_oriented'] for x in orbital):
        raise ValueError('用于体积演示的轨道等值面应闭合且方向一致')
    hs, ho, hv, atoms = cube(args.hs_dir/'surf.cub')
    if atoms.shape[0] != 6 or not np.array_equal(atoms[:, 0], [8, 1, 1, 8, 1, 1]):
        raise ValueError('本例 HS 分片和半径表限定为固定顺序的两个水分子')
    if not np.allclose(atoms, model_atoms):
        raise ValueError('HS 与域积分对应的原子模型不同')
    hs_mesh = mesh_metrics(hs, ho, hv, .5)
    pqr = [line.split() for line in (args.hs_dir/'vtx.pqr').read_text().splitlines() if line.startswith('HETATM')]
    pos = np.array([[float(x) for x in row[6:9]] for row in pqr])
    mapped = np.array([float(row[9]) for row in pqr])
    coord = atoms[:, 2:]*BOHR_A
    dist = np.linalg.norm(pos[:, None, :]-coord[None, :, :], axis=2)
    nearest_i, nearest_e = np.argmin(dist[:, :3], axis=1), np.argmin(dist[:, 3:], axis=1)+3
    di = dist[np.arange(len(pos)), nearest_i]
    de = dist[np.arange(len(pos)), nearest_e]
    radii = np.where(atoms[:, 0] == 1, 1.20, 1.52)
    standard = (di-radii[nearest_i])/radii[nearest_i] + (de-radii[nearest_e])/radii[nearest_e]
    # 2026.7.15 的 surfana_norm 对无量纲定义额外乘 b2a；核对版本差异。
    # PQR 坐标只保留0.001 Å；等距的异种原子可能因此交换最近原子身份。
    unique = (np.diff(np.sort(dist[:, :3], axis=1)[:, :2], axis=1)[:, 0] > .002) & (np.diff(np.sort(dist[:, 3:], axis=1)[:, :2], axis=1)[:, 0] > .002)
    if not unique.any():
        raise ValueError('没有可用于核对最近原子身份的表面点')
    err = float(np.max(abs(mapped[unique]-standard[unique]*BOHR_A)))
    if err > .002:
        raise ValueError('当前 d_norm 输出与本例已核对的实现不同，应重新核对版本及半径')
    fingerprint = np.loadtxt(args.hs_dir/'di_de_all.txt')
    if fingerprint.shape != (len(pos), 2) or np.max(abs(fingerprint-np.column_stack([di, de]))) > .001:
        raise ValueError('指纹距离与表面点重算不符')
    area_section = (args.hs_dir/args.log_name).read_text().split('Inside element, outside element,')[1].split('The same as above')[0]
    area_rows = re.findall(r'^\s*([HO]-[HO])\s+([\d.]+)\s+([\d.]+)\s*$', area_section, re.M)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    data = dict(
        model='Same fixed, unoptimized water dimer; PBE0/def2-SVP; no new electronic structure calculation',
        bin_order=['satt', 'matt', 'watt', 'rep'], bin_edges_au=[-.05, -.013, .009], IRI_level=1., IRI_exponent=1.1,
        connectivity=26, periodic=False, integration='uniform-grid node counting', domain_numbers='local script IDs; match other grids/programs by position, not ID', IRI=summary,
        orbital=dict(index=10, normalization='one spatial orbital, occupancy excluded', threshold_unit='Bohr^(-3/2)', meshes=orbital, Multiwfn_at_005=surface_log(args.orbital_dir/args.log_name)),
        HS=dict(fragment=[1, 2, 3], environment=[4, 5, 6], grid_spacing_Bohr=.3, box_vdw_multiplier=1.7, mesh=hs_mesh,
                Multiwfn=surface_log(args.hs_dir/args.log_name), contact_areas=[dict(pair=p, area_A2=float(a), percent=float(v)) for p, a, v in area_rows],
                dnorm_implementation='2026.7.15 multiplies the usual dimensionless formula by b2a; do not transfer numerical colour bounds blindly',
                maximum_dnorm_difference_for_unambiguous_rounded_coordinates=err,
                excluded_ambiguous_nearest_atom_checks=int((~unique).sum()), fingerprint_points=len(pos)),
        source_cube_sha256=hashes,
    )
    (out/'domain-analysis.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    np.savez_compressed(out/'domain-plot-data.npz', di_de_A=fingerprint, dnorm_standard=standard)
    print(json.dumps(dict(domain_counts={k: len(v['domains']) for k, v in summary.items()}, orbital=orbital, HS_closed=hs_mesh['closed'], dnorm_error=err), ensure_ascii=False))


if __name__ == '__main__':
    main()
