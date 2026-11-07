"""比较刚性/弛豫扫描与自由下坡；python analyze.py --work-root WORK --output-dir OUT。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from trajectory import angle, read_xyz, rows_for, write_csv
import prepare

HERE = Path(__file__).resolve().parent
HARTREE_EV = 27.211386245988


def energy(text):
    return float(re.findall(r'FINAL SINGLE POINT ENERGY\s+([-\d.]+)', text)[-1])


def normal(folder, optimization=False):
    text = (folder/'calc.out').read_text()
    if 'ORCA TERMINATED NORMALLY' not in text or 'error termination' in text:
        raise ValueError('原生任务没有正常结束')
    if optimization and 'THE OPTIMIZATION HAS CONVERGED' not in text:
        raise ValueError('相应优化未收敛')
    return text


def engrad(path):
    data = [line for line in path.read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')]
    n = int(data[0]); e = float(data[1]); grad = np.array(list(map(float, data[2:2+3*n]))).reshape(n, 3)
    rows = [line.split() for line in data[2+3*n:]]
    coords = np.array([list(map(float, row[1:])) for row in rows])
    if n != 3 or [int(row[0]) for row in rows] != [8, 1, 1]:
        raise ValueError('engrad原子不符')
    return e, grad, coords


def angle_jacobian(xyz):
    # Radian derivative in the same Cartesian length units as xyz.
    u, v = xyz[1]-xyz[0], xyz[2]-xyz[0]
    a, b = np.linalg.norm(u), np.linalg.norm(v); cosine = u@v/(a*b)
    sine = np.sqrt(1-cosine*cosine)
    du = -(v/(a*b)-cosine*u/(a*a))/sine
    dv = -(u/(a*b)-cosine*v/(b*b))/sine
    return np.array([-du-dv, du, dv])


def features(frame):
    xyz = np.array(frame['xyz_angstrom'])
    if frame['symbols'] != ['O', 'H', 'H']:
        raise ValueError('本例需要固定的OHH顺序')
    return {'OH_lengths_angstrom': [float(np.linalg.norm(xyz[i]-xyz[0])) for i in [1, 2]],
            'HOH_angle_degree': angle(xyz, 1, 0, 2)}


def analyze(root):
    cfg = json.loads((HERE/'protocol.json').read_text())
    expected = [{'path': f'a{a:g}/{m}', 'method': m, 'angle_degree': a} for a in cfg['angles_degree'] for m in ['rigid', 'relaxed']]
    expected += [{'path': mode, 'method': mode, 'angle_degree': cfg['angles_degree'][0]} for mode in ['free', 'downhill']]
    if json.loads((root/'jobs.json').read_text()) != expected:
        raise ValueError('任务清单与协议不一致')
    result = {'software': 'ORCA 6.1.1', 'protocol': cfg, 'source_sha256': {}, 'scan': [],
              'path_parameter': 'Native Cartesian gradient following; frame index and geometric descriptors are not time',
              'coordinate_precision': 'Native trajectory has six decimal places in angstrom; no extra geometry precision inferred'}
    all_jobs = expected+[{'path': 'down-end', 'method': 'free'}]
    for job in all_jobs:
        p = root/job['path']
        if (p/'calc.inp').read_bytes() != (HERE/f'{job["method"]}.inp').read_bytes():
            raise ValueError('原生输入与模板不符')
        if job['path'] != 'down-end' and (p/'structure.xyz').read_text() != prepare.water_xyz(job['angle_degree'], cfg['initial_OH_angstrom']):
            raise ValueError('初始结构与扫描协议不同')
        files = ['calc.inp', 'structure.xyz', 'calc.out']
        if job['method'] in ['relaxed', 'free']:files += ['calc.xyz', 'calc.engrad', 'calc_trj.xyz']
        if job['method'] == 'free':files += ['calc.hess']
        if job['method'] == 'downhill':files += ['calc_IRC_D.xyz', 'calc_IRC_D_trj.xyz']
        for name in files:result['source_sha256'][f'{job["path"]}/{name}'] = hashlib.sha256((p/name).read_bytes()).hexdigest()
    for a in cfg['angles_degree']:
        p = root/f'a{a:g}';er = energy(normal(p/'rigid'));el = energy(normal(p/'relaxed', optimization=True))
        final = read_xyz(p/'relaxed/calc.xyz', 'angstrom', 'orca')[0]
        f = features(final)
        if abs(f['HOH_angle_degree']-a) > 1e-5 or el > er+2e-9:
            raise ValueError('角度约束或弛豫能量检查失败')
        e, g, xyz = engrad(p/'relaxed/calc.engrad')
        j = angle_jacobian(xyz); multiplier = float(np.sum(g*j)/np.sum(j*j))
        projected = g-multiplier*j
        result['scan'].append({'angle_degree': a, 'rigid_energy_Ha': er, 'relaxed_energy_Ha': el,
                               'relaxation_lowering_eV': (er-el)*HARTREE_EV, **f,
                               'unprojected_gradient_norm_Ha_per_Bohr': float(np.linalg.norm(g)),
                               'allowed_gradient_norm_Ha_per_Bohr': float(np.linalg.norm(projected)),
                               'constraint_multiplier_Ha_per_radian': multiplier})
    free = root/'free'; end = root/'down-end';down = root/'downhill'
    result['free_energy_Ha'] = energy(normal(free, optimization=True))
    result['downhill_endpoint_energy_Ha'] = energy(normal(end, optimization=True))
    result['free_geometry'] = features(read_xyz(free/'calc.xyz', 'angstrom', 'orca')[0])
    result['downhill_endpoint_geometry'] = features(read_xyz(end/'calc.xyz', 'angstrom', 'orca')[0])
    for name, p in [('free', free), ('down-end', end)]:
        lines = (p/'calc.hess').read_text().splitlines();i = lines.index('$vibrational_frequencies')+1
        n = int(lines[i]);freq = [float(lines[i+1+k].split()[1]) for k in range(n)]
        if n != 9 or min(freq[6:]) <= 0:raise ValueError('端点内部频率不是全部正值')
        result[name+'_internal_frequencies_cm-1'] = freq[6:]
    text = normal(down)
    if text.count('THE IRC HAS CONVERGED') != 1:raise ValueError('单向downhill未收敛')
    block = text.split('Iteration    E(Eh)', 1)[1].split('HURRAY', 1)[0]
    table = re.findall(r'^\s*(\d+)\s+(-[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$', block, re.M)
    frames = read_xyz(down/'calc_IRC_D_trj.xyz', 'angstrom', 'orca')
    if len(frames) != len(table) or float(table[-1][-2]) > 3e-5 or float(table[-1][-1]) > 1e-5:
        raise ValueError('原生接受点与收敛判据不符')
    if not np.allclose(read_xyz(end/'structure.xyz', 'angstrom', 'orca')[0]['xyz_angstrom'], frames[-1]['xyz_angstrom'], atol=5.1e-7, rtol=0):
        raise ValueError('末点优化的起始结构不同')
    if abs(frames[0]['energy_Ha']-result['scan'][0]['rigid_energy_Ha']) > 1e-9:
        raise ValueError('下坡与扫描起点能量不同')
    if np.max(np.diff([f['energy_Ha'] for f in frames])) > 2e-10:
        raise ValueError('接受点路径有不合理升能')
    result['downhill_final_max_gradient_Ha_per_Bohr'] = float(table[-1][-2])
    result['downhill_final_rms_gradient_Ha_per_Bohr'] = float(table[-1][-1])
    result['downhill_frames'] = frames
    result['optimization_frames'] = read_xyz(free/'calc_trj.xyz', 'angstrom', 'orca')
    result['downhill_last_optimization_lowering_Ha'] = frames[-1]['energy_Ha']-result['downhill_endpoint_energy_Ha']
    return result


def branch_potential(x, y):
    return .25*(y*y-1)**2-x*y+.2*x*x


def branch_model():
    xs = np.linspace(-.6, .6, 121)
    possible = []
    for x in xs:
        roots = np.roots([1, 0, -1, -x])
        minima = sorted(float(v.real) for v in roots if abs(v.imag)<1e-9 and 3*v.real*v.real-1>0)
        possible.append(minima)
    def follow(order):
        previous = None; ys = np.empty(len(xs))
        for i in order:
            roots = possible[i]
            y = roots[0] if previous is None else min(roots, key=lambda y: abs(y-previous))
            ys[i] = y;previous = y
        return ys
    forward, reverse = follow(range(len(xs))), follow(range(len(xs)-1, -1, -1))
    global_y = np.array([min(roots, key=lambda y: branch_potential(x,y)) for x, roots in zip(xs,possible)])
    return {'kind': 'Dimensionless algebraic constrained-minimum branch continuation; not a molecular calculation or universal optimizer model',
            'potential': '(y^2-1)^2/4 - x*y + 0.2*x^2', 'x': xs.tolist(),
            'forward_y': forward.tolist(), 'reverse_y': reverse.tolist(), 'global_minimum_y': global_y.tolist(),
            'forward_energy': branch_potential(xs,forward).tolist(), 'reverse_energy': branch_potential(xs,reverse).tolist(),
            'global_minimum_energy': branch_potential(xs,global_y).tolist(), 'spinodal_abs_x': float(2/(3*np.sqrt(3)))}


def main():
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('--work-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a = p.parse_args()
    r = analyze(a.work_root);a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'analysis.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    for name, source in [('downhill',a.work_root/'downhill/calc_IRC_D_trj.xyz'),('optimization',a.work_root/'free/calc_trj.xyz')]:
        shutil.copy2(source,a.output_dir/f'{name}.xyz')
        write_csv(a.output_dir/f'{name}.csv',rows_for(r[name+'_frames'],[(1,2),(1,3)],[(2,1,3)]))
    fig, axes = plt.subplots(1,2,figsize=(10,4),layout='constrained')
    scan = r['scan'];angles = [s['angle_degree'] for s in scan]
    for label,key in [('Rigid: OH=1 A','rigid_energy_Ha'),('Constrained relaxation','relaxed_energy_Ha')]:
        axes[0].plot(angles,[(s[key]-r['free_energy_Ha'])*HARTREE_EV for s in scan],'o-',label=label)
    axes[0].set(xlabel='Fixed H-O-H angle / degree',ylabel='E - free minimum / eV',title='H2O: same RHF/def2-SVP surface');axes[0].legend(fontsize=8)
    for name,label in [('downhill','Native Cartesian downhill'),('optimization','Geometry optimizer')]:
        f = [features(fr) for fr in r[name+'_frames']]
        axes[1].plot([v['HOH_angle_degree'] for v in f],[np.mean(v['OH_lengths_angstrom']) for v in f],'o-',ms=3,label=label)
    axes[1].set(xlabel='H-O-H angle / degree',ylabel='Mean O-H length / angstrom',title='Same start, different geometry paths');axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(alpha=.2)
    fig.savefig(a.output_dir/'scan-and-descent.png',dpi=180,metadata={'Software':'Matplotlib'});plt.close(fig)
    model = branch_model();(a.output_dir/'branch-model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
    fig, axes = plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
    for name,label in [('forward','Increasing x'),('reverse','Decreasing x'),('global_minimum','Global envelope')]:
        axes[0].plot(model['x'],model[name+'_y'],label=label,ls='--' if name=='global_minimum' else '-')
        axes[1].plot(model['x'],model[name+'_energy'],label=label,ls='--' if name=='global_minimum' else '-')
    axes[0].set(xlabel='Constrained x / model coordinate',ylabel='Locally relaxed y',title='Algebraic model: branch and direction')
    axes[1].set(xlabel='Constrained x / model coordinate',ylabel='Model potential energy',title='Local branches need not be the lower envelope')
    for ax in axes:ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.savefig(a.output_dir/'scan-branch-model.png',dpi=180,metadata={'Software':'Matplotlib'});plt.close(fig)
    print(json.dumps({'scan':r['scan'],'free_geometry':r['free_geometry'],'free_energy_Ha':r['free_energy_Ha'],'downhill_frames':len(r['downhill_frames']),'optimizer_frames':len(r['optimization_frames'])},ensure_ascii=False))


if __name__ == '__main__':
    main()
