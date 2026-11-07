"""提取周期水二聚体的 TDA/NTO 和 NCI/IGMH；用法：python analyze.py --work-root WORK --output-dir OUT。"""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

B2A = 0.529177210903


def load_cube_reader():
    source = Path(__file__).resolve().parents[3] / 'orca/minimal/weak-interactions/analyze.py'
    spec = importlib.util.spec_from_file_location('weak_fields', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.cube


def excitations(text, nocc, nmo):
    if 'SCF run converged' not in text or 'PROGRAM ENDED AT' not in text:
        raise ValueError('缺少正常完成的 SCF/程序记录')
    if not re.search(r'TDDFPT.*converged', text, re.I):
        raise ValueError('缺少 TDDFPT 收敛记录')
    number = r'[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?'
    rows = re.findall(r'^ TDDFPT\|[ \t]+(\d+)[ \t]+('+number+r')[ \t]+'+number+r'[ \t]+'+number+r'[ \t]+'+number+r'[ \t]+('+number+r')[ \t]*$', text, re.M)
    parts = re.split(r'^\s+(\d+)\s+([\d.]+) eV\s*$', text, flags=re.M)
    matrices = {}
    for k in range(1, len(parts), 3):
        state = int(parts[k])
        t = np.zeros((nocc, nmo-nocc))
        for i, a, value in re.findall(r'^\s+(\d+)\s+(\d+)\s+(-?[\d.]+)\s*$', parts[k+2], re.M):
            i, a = int(i), int(a)
            if not 1 <= i <= nocc or not nocc < a <= nmo:
                raise ValueError('跃迁索引超出导出的轨道空间')
            t[i-1, a-nocc-1] = float(value)
        if not np.isclose(np.sum(t*t), 1, atol=3e-6):
            raise ValueError('打印系数的范数不接近 1；检查阈值与自旋约定')
        matrices[state] = t
    if set(matrices) != {int(row[0]) for row in rows} or not rows:
        raise ValueError('激发能与系数的态数不匹配')
    return [dict(state=int(i), energy_ev=float(e), oscillator_strength=float(f),
                 printed_norm=float(np.sum(matrices[int(i)]**2)),
                 nto_weights=(np.linalg.svd(matrices[int(i)], compute_uv=False)**2).tolist())
            for i, e, f in rows], matrices


def main(work, out):
    out.mkdir(parents=True, exist_ok=True)
    cube = load_cube_reader()
    molden = (work/'grid/periodic.molden').read_text()
    occup = [float(v) for v in re.findall(r'Occup\s*=\s*(\S+)', molden)]
    if len(occup) != 46 or sum(occup) != 16 or occup[:8] != [2]*8 or any(occup[8:]):
        raise ValueError('此示例要求 46 轨道、16 电子及闭壳层整数占据')
    log = (work/'periodic-tddfpt/cp2k.out').read_text()
    states, matrices = excitations(log, 8, 46)
    native = np.array([float(v) for v in re.findall(r'^Energy=\s*(\S+)', (work/'nto/nto.mwfn').read_text(), re.M)])
    weights = np.array(states[0]['nto_weights'])
    error = float(np.max(abs(native[8:16] - weights)))
    if error > 2e-8 or abs(native[8:].sum()-weights.sum()) > 2e-8:
        raise ValueError('独立 SVD 与原生 NTO 不一致')
    fields = {}
    for label, files in {'grid':['func1.cub','func2.cub'], 'igmh':['dg_inter.cub','sl2r.cub']}.items():
        shifted = 'translated' if label == 'grid' else 'igmh-translated'
        for name in files:
            data, origin, vectors, atoms = cube(work/label/name)
            translated, origin2, vectors2, _ = cube(work/shifted/name)
            if not np.allclose(vectors, vectors2) or not np.allclose(origin2-origin, [8/B2A,0,0], atol=2e-6):
                raise ValueError('网格平移/步进矢量不一致')
            maxdiff = float(np.max(abs(data-translated)))
            if maxdiff > 1e-9:
                raise ValueError('晶胞平移后场值不一致')
            fields[label+'/'+name] = dict(shape=list(data.shape), max_translation_difference=maxdiff)
        analysis_log = (work/label/'multiwfn.out').read_text()
        if 'Net charge:     0.00000' not in analysis_log:
            raise ValueError('赝势电荷元数据读取错误')
    rdg, origin, vectors, atoms = cube(work/'grid-fine/func2.cub')
    sl2r, o2, v2, _ = cube(work/'grid-fine/func1.cub')
    igmh, o3, v3, _ = cube(work/'igmh-fine/dg_inter.cub')
    if not np.allclose(origin,o2) or not np.allclose(origin,o3) or not np.allclose(vectors,v2) or not np.allclose(vectors,v3):
        raise ValueError('细网格未对齐')
    z = int(np.argmin(abs((origin[2]+np.arange(rdg.shape[2])*vectors[2,2])*B2A-3)))
    x = (origin[0]+np.arange(rdg.shape[0])*vectors[0,0])*B2A
    y = (origin[1]+np.arange(rdg.shape[1])*vectors[1,1])*B2A
    fig, axes = plt.subplots(1, 2, figsize=(9,3.6), constrained_layout=True)
    mask = rdg[:,:,z] < 0.5
    plotted = np.ma.masked_where(~mask, sl2r[:,:,z])
    img = axes[0].pcolormesh(x,y,plotted.T,vmin=-.04,vmax=.04,cmap='bwr',shading='nearest')
    fig.colorbar(img, ax=axes[0], label=r'$\mathrm{sign}(\lambda_2)\rho$ (a.u.)')
    img = axes[1].pcolormesh(x,y,igmh[:,:,z].T,cmap='viridis',shading='nearest')
    fig.colorbar(img, ax=axes[1], label=r'$\delta g_{\mathrm{inter}}$ (a.u.)')
    for ax, title in zip(axes, ['NCI: RDG < 0.5','IGMH: fragments 1-3 / 4-6']):
        ax.set(title=title, xlabel='x (Å)',ylabel='y (Å)',aspect='equal')
        for atom in atoms:
            # Cube 读取器返回原子序数、核电荷与坐标。
            ax.scatter(atom[2]*B2A,atom[3]*B2A,c='red' if atom[0]==8 else 'white',edgecolors='black',s=35)
    fig.suptitle(f'Periodic water dimer; z = {(origin[2]+z*vectors[2,2])*B2A:.3f} Å; grid 0.2 bohr')
    fig.savefig(out/'periodic-fields.png', dpi=170);plt.close(fig)
    e = np.array([s['energy_ev'] for s in states]); f = np.array([s['oscillator_strength'] for s in states])
    grid = np.linspace(8, 12.5, 1801); sigma=.15
    spectrum = np.sum(f[:,None]*np.exp(-.5*((grid[None,:]-e[:,None])/sigma)**2)/(sigma*np.sqrt(2*np.pi)),axis=0)
    fig, axes = plt.subplots(1,2,figsize=(9,3.4),constrained_layout=True)
    axes[0].plot(grid,spectrum,label='Gaussian σ = 0.15 eV');axes[0].vlines(e,0,f/(sigma*np.sqrt(2*np.pi)),color='tab:orange')
    axes[0].set(xlabel='Excitation energy (eV)',ylabel='Oscillator-strength density (eV⁻¹)');axes[0].legend(fontsize=8)
    for s in states:
        axes[1].plot(np.arange(1,9),s['nto_weights'],marker='o',label=f"State {s['state']}")
    axes[1].set(xlabel='NTO pair rank',ylabel='Weight',yscale='log',ylim=(1e-7,2));axes[1].legend(fontsize=8)
    fig.savefig(out/'periodic-excitations.png',dpi=170);plt.close(fig)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(model='fixed water dimer, 8 Angstrom cubic cell, Gamma, PBE/DZVP-MOLOPT-SR-GTH, GTH O q6/H q1',
                versions=dict(cp2k='2026.2',multiwfn='2026.7.15'),
                input_sha256=sha(work/'periodic-tddfpt/cp2k.inp'),geometry_sha256=sha(work/'periodic-tddfpt/structure.xyz'),
                wavefunction_sha256=sha(work/'periodic-tddfpt/optical-MOS-1_0.molden'),
                analysis_wavefunction_sha256=sha(work/'grid/periodic.molden'),
                nmo=46,electrons=16,states=states,native_nto_max_abs_error=error,fields=fields,
                broadening_sigma_ev=sigma,grid_spacing_bohr=.2,
                limitations=['Finite image-summation defaults retained; translation equality does not establish image convergence',
                             'Compact basis, fixed artificial cell, three roots; no converged material absorption spectrum'])
    (out/'response.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'response.npz',rdg=rdg,sign_lambda2_rho=sl2r,igmh=igmh,
                        origin_bohr=origin,vectors_bohr=vectors,energy_grid_ev=grid,spectrum=spectrum,
                        **{f'transition_{k}':v for k,v in matrices.items()})
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();main(args.work_root,args.output_dir)
