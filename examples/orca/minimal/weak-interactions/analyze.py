"""读取本例 IGMH Cube，保存小型表面/切片数据与科学条件。

用法：python analyze.py --grid-dir . --orca-output orca.out \
    --multiwfn-output multiwfn.out --wavefunction orca.molden.input
等值面单位为 e/Bohr^4；本例只接受单标量、正交且以 Bohr 记录的 Cube。
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from skimage.measure import marching_cubes

BOHR_A = 0.529177210903


def cube(path):
    lines = path.read_text().splitlines()
    first = lines[2].split()
    natom = int(first[0])
    origin = np.array(first[1:4], dtype=float)
    shape = np.array([int(lines[i].split()[0]) for i in [3, 4, 5]])
    vectors = np.array([lines[i].split()[1:4] for i in [3, 4, 5]], dtype=float)
    if natom <= 0 or np.any(shape <= 0) or len(first) > 4 and int(first[4]) != 1:
        raise ValueError('本例需要单标量、坐标单位为 Bohr 的 Cube')
    if not np.allclose(vectors, np.diag(np.diag(vectors))) or np.any(np.diag(vectors) <= 0):
        raise ValueError('本例绘图限于沿正笛卡尔方向的正交网格')
    atoms = np.array([line.split() for line in lines[6:6+natom]], dtype=float)
    values = np.fromstring(' '.join(lines[6+natom:]), sep=' ')
    if len(values) != np.prod(shape) or not np.isfinite(values).all():
        raise ValueError('Cube 数据数量或有限性检查失败')
    return values.reshape(shape), origin, vectors, atoms


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--grid-dir', type=Path, default=Path('.'))
    ap.add_argument('--orca-output', type=Path, required=True)
    ap.add_argument('--multiwfn-output', type=Path, required=True)
    ap.add_argument('--wavefunction', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, default=Path('.'))
    ap.add_argument('--isovalue', type=float, default=.006)
    args = ap.parse_args()
    grid = args.grid_dir
    field, origin, vectors, atoms = cube(grid/'dg_inter.cub')
    colour, origin2, vectors2, atoms2 = cube(grid/'sl2r.cub')
    if field.shape != colour.shape or not np.allclose(origin, origin2) or not np.allclose(vectors, vectors2) or not np.allclose(atoms, atoms2):
        raise ValueError('等值面与着色网格不匹配')
    if field.min() < -1e-10 or not field.min() < args.isovalue < field.max():
        raise ValueError('delta-g_inter 范围或等值面数值不合适')
    step = np.diag(vectors)
    index_vertices, faces, _, _ = marching_cubes(field, level=args.isovalue, allow_degenerate=False)
    interpolation = RegularGridInterpolator(tuple(np.arange(n) for n in field.shape), colour)
    surface_colour = interpolation(index_vertices)
    vertices_A = (origin + index_vertices*step)*BOHR_A
    plane_index = int(np.argmin(abs(origin[2] + np.arange(field.shape[2])*step[2])))
    boundary_max = float(max(field[0].max(), field[-1].max(), field[:,0].max(), field[:,-1].max(), field[:,:,0].max(), field[:,:,-1].max()))
    orca = args.orca_output.read_text()
    mw = args.multiwfn_output.read_text()
    if 'ORCA TERMINATED NORMALLY' not in orca:
        raise ValueError('ORCA 日志未正常结束')
    if 'delta-g_inter has been exported' not in mw:
        raise ValueError('Multiwfn 日志没有对应导出记录')
    energy = float(re.findall(r'FINAL SINGLE POINT ENERGY\s+([-\d.]+)', orca)[-1])
    version = re.search(r'Version\s+(\d+\.\d+\.\d+)', mw)[1]
    pairgrid = re.search(r'Radial points:\s*(\d+)\s+Angular points:\s*(\d+)', mw)
    if pairgrid is None:
        raise ValueError('日志缺少原子对指标所用积分网格')
    screening = re.search(r'Prescreening grids with IGMvdwscl parameter:\s*([\d.]+)', mw)
    pairtext = (grid/'atmdg.txt').read_text()
    pairs = [dict(atoms=[int(i),int(j)], index_e_Bohr=float(v), percent=float(p)) for i,j,v,p in re.findall(r'^\s*(\d+)\s+(\d+)\s*:\s*([\d.]+)\s*\(\s*([\d.]+)', pairtext, re.M)]
    atom_indices = [dict(atom=int(i), index_e_Bohr=float(v), percent_in_own_fragment=float(p)) for i,v,p in re.findall(r'^\s*Atom\s+(\d+)\s*:\s*([\d.]+)\s*\(\s*([\d.]+)', pairtext, re.M)]
    totalpair = float(re.search(r'Sum of all atomic pair delta-g indices:\s*([\d.]+)', pairtext)[1])
    if len(pairs) != 9 or len(atom_indices) != 6 or abs(sum(v['index_e_Bohr'] for v in pairs)-totalpair) > 1e-5:
        raise ValueError('本例原子对表不完整或求和不一致')
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out/'interaction-data.npz', vertices_A=vertices_A, faces=faces, surface_colour=surface_colour, atoms_A=np.column_stack([atoms[:,0],atoms[:,2:]*BOHR_A]), x_A=(origin[0]+np.arange(field.shape[0])*step[0])*BOHR_A, y_A=(origin[1]+np.arange(field.shape[1])*step[1])*BOHR_A, delta_g_plane=field[:,:,plane_index], colour_plane=colour[:,:,plane_index])
    metadata = dict(
        system='Planar water dimer teaching geometry; O-O 2.9 Angstrom; no geometry optimization',
        electronic_structure=dict(
            program='ORCA 6.1.1', method='PBE0', basis='def2-SVP',
            charge=0, multiplicity=1, SCF='TightSCF', energy_Ha=energy,
        ),
        analyzer=f'Multiwfn {version}',
        fragments=[[1,2,3],[4,5,6]],
        grid=dict(
            shape=list(map(int,field.shape)), origin_Bohr=origin.tolist(),
            vectors_Bohr=vectors.tolist(),
            IGMvdwscl=float(screening[1]) if screening else 0.,
            delta_g_inter_integral_e_Bohr=float(field.sum()*np.linalg.det(vectors)),
            integral_domain='finite exported box; prescreened points are zero when IGMvdwscl is nonzero',
            boundary_delta_g_inter_max_e_Bohr4=boundary_max,
        ),
        surface=dict(
            isovalue_e_Bohr4=args.isovalue, colour='sign(lambda2)rho, e/Bohr^3',
            colour_range=[-.04,.04], vertices=len(vertices_A), triangles=len(faces),
            boundary_below_isovalue=boundary_max<args.isovalue,
        ),
        slice=dict(
            z_A=float((origin[2]+plane_index*step[2])*BOHR_A),
            interpolation='nearest actual z grid layer; no interpolation of slice',
        ),
        atomic_pair_quadrature=dict(
            radial=int(pairgrid[1]), angular=int(pairgrid[2]), index_unit='e/Bohr',
            pairs=pairs, atoms=atom_indices, pair_sum_e_Bohr=totalpair,
        ),
        sha256=dict(
            dg_inter_cube=sha(grid/'dg_inter.cub'), sl2r_cube=sha(grid/'sl2r.cub'),
            molden=sha(args.wavefunction),
        ),
    )
    (out/'interaction-analysis.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(grid=metadata['grid'],surface=metadata['surface'],slice=metadata['slice']),ensure_ascii=False))


if __name__ == '__main__':
    main()
