"""核对内切球、势场CP和同入口逐帧amIGM平均。

从仓库调用：python examples/multiwfn/diameter-extrema-average/analyze.py \
    --work-root WORK --output-dir OUT --log-name multiwfn.out
模型和原子顺序固定；三帧刚性水构型只用于验证平均，不是MD轨迹。
"""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import numpy as np

reader = Path(__file__).resolve().parents[2]/'orca/minimal/weak-interactions/analyze.py'
spec = importlib.util.spec_from_file_location('dimer_reader', reader)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
cube, BOHR_A = module.cube, module.BOHR_A


def properties(path, mode):
    rows = []
    for block in re.split(r'-+\s+CP\s+\d+,.*?-+\n', path.read_text())[1:]:
        find = lambda pattern: re.search(pattern, block)[1]
        coord = np.fromstring(find(r'Position \(Angstrom\):\s*([^\n]+)'), sep=' ')
        gradient = np.fromstring(find(r'Components of gradient in x/y/z are:\s*([^\n]+)'), sep=' ')
        matrix = np.array([np.fromstring(line, sep=' ') for line in find(r'Hessian matrix:\s*([^\n]+\n[^\n]+\n[^\n]+)').splitlines()])
        eig = np.fromstring(find(r'Eigenvalues of Hessian:\s*([^\n]+)'), sep=' ')
        if coord.size != 3 or gradient.size != 3 or matrix.shape != (3, 3) or eig.size != 3:
            raise ValueError('CP属性列数不符')
        if not np.allclose(np.linalg.eigvalsh(matrix), eig, rtol=2e-8, atol=1e-10) or np.any(eig <= 0) or np.linalg.norm(gradient) > 1e-5:
            raise ValueError('本例所选CP应满足低梯度且Hessian正定')
        if mode == 'ESP':
            value = float(find(r'Total ESP:\s*([\d.E+-]+)'))
            density = float(find(r'Density of all electrons:\s*([\d.E+-]+)'))
        else:
            value = float(find(r'van der Waals potential[^\n]*:\s*([\d.E+-]+)\s*kcal/mol'))
            density = None
        row = dict(position_A=coord.tolist(), value=value, gradient_Bohr=gradient.tolist(), hessian_Bohr2=matrix.tolist(), eigenvalues_Bohr2=eig.tolist(), density_e_Bohr3=density)
        if mode == 'ESP':
            # 此版本ESP的Hessian来自数值差分；记录解析关系的偏差，不当作输出精度的恒等式。
            row['poisson_relative_residual'] = float((np.trace(matrix)-4*np.pi*density)/(4*np.pi*density))
        rows.append(row)
    if not rows:
        raise ValueError('没有CP属性，不能仅凭退出码认为搜索成功')
    return rows


def octahedral_uff(point):
    atoms = np.concatenate([np.eye(3)*4, -np.eye(3)*4])
    delta = point-atoms
    radius = np.linalg.norm(delta, axis=1)
    unit = delta/radius[:, None]
    epsilon, R0 = (.185*.105)**.5, (3.868*3.851)**.5
    x6 = (R0/radius)**6
    value = np.sum(epsilon*(x6*x6-2*x6))
    first = 12*epsilon*(x6-x6*x6)/radius
    second = 12*epsilon*(-7*x6+13*x6*x6)/radius**2
    grad = (first[:, None]*unit).sum(axis=0)*BOHR_A
    hess = sum(second[i]*np.outer(u, u)+first[i]/radius[i]*(np.eye(3)-np.outer(u, u)) for i, u in enumerate(unit))*BOHR_A**2
    return float(value), grad, hess


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work-root', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--log-name', default='multiwfn.out')
    args = ap.parse_args()
    root = args.work_root
    diameters = {}
    expected = {'diameter-cage': .5, 'diameter-ring': 1.3, 'diameter-ring-above': 13**.5-1.7, 'diameter-periodic': 48**.5-1.88}
    for name, value in expected.items():
        text = (root/name/args.log_name).read_text()
        radius = float(re.search(r'Radius is\s*([\d.]+)', text)[1])
        diameter = float(re.search(r'Diameter is\s*([\d.]+)', text)[1])
        volume = float(re.search(r'Volume is\s*([\d.]+)', text)[1])
        if abs(radius-value) > 6e-7 or abs(diameter-2*value) > 1.1e-6:
            raise ValueError('原生内切球结果与独立几何式不符')
        diameters[name] = dict(radius_A=radius, diameter_A=diameter, sphere_volume_A3=volume, analytic_radius_A=value)
    esp = properties(root/'esp/CPprop.txt', 'ESP')
    uff = properties(root/'uff-minima/CPprop.txt', 'UFF')
    if len(esp) != 4 or len(uff) != 1:
        raise ValueError('本例固定初猜集合的CP数量与记录不同，应重新核对')
    expected_value, expected_grad, expected_hess = octahedral_uff(np.array(uff[0]['position_A']))
    if not np.isclose(uff[0]['value'], expected_value, rtol=0, atol=1e-9) or not np.allclose(uff[0]['hessian_Bohr2'], expected_hess, rtol=0, atol=1e-9) or not np.allclose(uff[0]['gradient_Bohr'], expected_grad, rtol=0, atol=1e-10):
        raise ValueError('UFF原生CP性质与独立解析导数不符')
    static = dict(diameter_models='Same idealC20, planar C12R3A, single-Ar8A periodic cell; no optimized phase claim', diameters=diameters,
                  ESP=dict(model='Fixed water dimer PBE0/def2-SVP', value_unit='atomic potential units', derivative_units='atomic potential units perBohr/perBohr2', CPs=esp),
                  UFF=dict(model='Fixed6Ar at ±4A axes, defaultC probe', value_unit='kcal/mol', derivative_units='kcal/mol perBohr/perBohr2', CPs=uff),
                  search_scope='Given deterministic starting points only; neither full extrema coverage nor adsorption equilibria asserted')
    avg, origin, vectors, atoms = cube(root/'average/avgdg_inter.cub')
    colour, co, cv, ca = cube(root/'average/avgsl2r.cub')
    fields, colours, hashes = [], [], {}
    for i in [1, 2, 3]:
        path = root/f'am-frame-{i}'/'avgdg_inter.cub'
        field, o, v, a = cube(path)
        s, so, sv, sa = cube(root/f'am-frame-{i}'/'avgsl2r.cub')
        if colour.shape != avg.shape or field.shape != avg.shape or s.shape != avg.shape or not all(np.allclose(x, y) for x, y in [(origin, o), (origin, so), (vectors, v), (vectors, sv), (co, origin), (cv, vectors), (ca, atoms), (atoms[:3], a[:3]), (a, sa)]):
            raise ValueError('平均场与逐帧场的网格或参考片段不匹配')
        fields.append(field); colours.append(s); hashes[f'frame{i}'] = hashlib.sha256(path.read_bytes()).hexdigest()
    fields = np.array(fields)
    mean = fields.mean(axis=0)
    std = fields.std(axis=0, ddof=0)
    if np.max(abs(mean-avg)) > 1e-7:
        raise ValueError('同入口逐帧算术平均与原生amIGM不符')
    if not re.search(r'Final percent of screened grids:\s*0.00%', (root/'average'/args.log_name).read_text()):
        raise ValueError('本例局部网格应未被几何预筛选，不能改变积分范围后直接比较')
    positive = mean > 0
    tfi = np.full(mean.shape, np.nan)
    tfi[positive] = std[positive]/mean[positive]
    z = int(np.argmin(abs(origin[2]+np.arange(avg.shape[2])*vectors[2, 2])))
    info = dict(model='Three constructed rigid-water snapshots, not MD; first water fixed; second water translated0,+0.3,-0.3A inY',
                frame_count=3, grid=dict(shape=list(avg.shape), origin_Bohr=origin.tolist(), vectors_Bohr=vectors.tolist()),
                mean_definition='arithmetic mean of per-frame delta-g, same amIGM implementation per frame', std_definition='population standard deviation, ddof0',
                mean_max_difference=float(np.max(abs(mean-avg))), mean_geometry_max_difference=float(np.max(abs(avg-fields[0]))),
                colour_mean_difference=float(np.max(abs(colour-np.mean(colours, axis=0)))),
                colour_definition='sign(lambda2(mean Hessian of promolecular density))*mean promolecular density, not mean of framewise signed density',
                minimum_mean=float(mean.min()), maximum_std=float(std.max()), local_integral_e_Bohr=float(avg.sum()*abs(np.linalg.det(vectors))),
                sigma_TFI_implementation='Postprocessing of native single-frame amIGM fields; population std, ddof0', software_version='Multiwfn2026.7.15',
                displayed_mean_threshold=.003, z_slice_A=float((origin[2]+z*vectors[2, 2])*BOHR_A), source_delta_grid_sha256=hashes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'diameter-extrema.json').write_text(json.dumps(static, ensure_ascii=False, indent=2)+'\n')
    (args.output_dir/'average-analysis.json').write_text(json.dumps(info, ensure_ascii=False, indent=2)+'\n')
    np.savez_compressed(args.output_dir/'average-data.npz', mean=avg, mean_geometry=fields[0], std=std, tfi=tfi, colour=colour,
                        origin_Bohr=origin, vectors_Bohr=vectors, z_index=z)
    print(json.dumps(dict(esp_points=len(esp), UFF_minimum=uff[0]['value'], mean_delta_error=info['mean_max_difference'], colour_noncommutation=info['colour_mean_difference']), ensure_ascii=False))


if __name__ == '__main__':
    main()
