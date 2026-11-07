"""重建空穴/电子、NTO、IFCT；用法：python analyze.py --work-root WORK --response OUT --output-dir DERIVED。"""
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


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def helpers():
    examples = Path(__file__).resolve().parents[2]
    response = module('periodic_response', examples/'cp2k/minimal/periodic-response/analyze.py')
    ao = module('ao_readers', examples/'orca/minimal/orbital-dos-cda/analyze.py')
    return response, ao


def cube_roundoff(values):
    """原生 Cube 的六位有效数字给出逐点半末位界。"""
    return np.where(values==0,0,.51*10.**(np.floor(np.log10(np.maximum(abs(values),1e-290)))-5))


def moments(h, e, origin, vectors):
    if not np.isfinite(h).all() or not np.isfinite(e).all() or min(h.min(),e.min()) < 0:
        raise ValueError('空穴/电子网格存在非有限或负值')
    dv = abs(np.linalg.det(vectors))
    points = origin+np.indices(h.shape).reshape(3,-1).T@vectors
    result = {}
    for name, field in [('hole',h),('electron',e)]:
        weight = field.ravel()*dv
        norm = weight.sum()
        if norm <= 0:
            raise ValueError('空分布不能计算空间指标')
        centre = weight@points/norm
        d = points-centre
        cov = (d.T*weight)@d/norm
        result[name] = dict(integral=float(norm),centroid_angstrom=(centre*B2A).tolist(),
                            sigma_angstrom=(np.sqrt(np.diag(cov))*B2A).tolist(),
                            covariance_bohr2=cov.tolist(),
                            delocalization_index_au=float(100*np.sqrt(np.sum(field**2)*dv)))
    result['Sm'] = float(np.minimum(h,e).sum()*dv)
    result['Sr'] = float(np.sqrt(h*e).sum()*dv)
    a = result['hole'];b = result['electron']
    d = np.array(b['centroid_angstrom'])-a['centroid_angstrom']
    result['D_angstrom'] = float(np.linalg.norm(d))
    return result


def native_atomic_mulliken(x, c, s, owner, product_cutoff):
    # CP2K X 范数为 1，原生闭壳层幅度为 X/√2，乘积阈值相应乘 2。
    h = np.array([[np.sum(np.where(abs(x[i]*x[j]) >= 2*product_cutoff, x[i]*x[j],0))
                   for j in range(8)] for i in range(8)])
    e = np.array([[np.sum(np.where(abs(x[:,i]*x[:,j]) >= 2*product_cutoff, x[:,i]*x[:,j],0))
                   for j in range(38)] for i in range(38)])
    populations = []
    for coeff, q in [(c[:,:8],h),(c[:,8:],e)]:
        pop = np.diag(coeff@q@coeff.T@s)
        atom = np.array([pop[owner==i].sum() for i in range(1,7)])
        populations.append(atom/atom.sum())
    return populations


def main(work, response_file, out):
    out.mkdir(parents=True,exist_ok=True)
    response, ao = helpers();cube = response.load_cube_reader()
    states, matrices = response.excitations(response_file.read_text(),8,46)
    x = matrices[3]
    for folder in work.iterdir():
        if not folder.is_dir() or not (folder/'multiwfn.out').exists():continue
        log = (folder/'multiwfn.out').read_text()
        if 'Fortran runtime error' in log or 'SIGSEGV' in log or 'NaN' in log or 'Infinity' in log:
            raise ValueError(f'{folder.name} 原生输出异常')
    convergence = {}
    slices = {}
    fig, axes = plt.subplots(1,3,figsize=(10.5,3.8),constrained_layout=True)
    for n in [32,48,64]:
        h,o,v,atoms = cube(work/f'hole-{n}/hole.cub')
        e,o2,v2,_ = cube(work/f'hole-{n}/electron.cub')
        if h.shape != (n,n,n) or not np.allclose(o,o2) or not np.allclose(v,v2):
            raise ValueError('空穴/电子网格不对应')
        convergence[n] = moments(h,e,o,v)
        if not convergence[n]['Sm'] <= convergence[n]['Sr'] <= np.sqrt(convergence[n]['hole']['integral']*convergence[n]['electron']['integral'])+1e-9:
            raise ValueError('重叠积分不满足非负密度的界限')
        for file,expected in [('Sm.cub',np.minimum(h,e)),('Sr.cub',np.sqrt(h*e)),('CDD.cub',e-h)]:
            actual,oo,vv,_ = cube(work/f'hole-{n}'/file)
            values_ok = (np.all(abs(actual-expected) <= cube_roundoff(h)+cube_roundoff(e)+cube_roundoff(actual)+1e-14)
                         if file=='CDD.cub' else np.allclose(actual,expected,rtol=1.2e-5,atol=1e-8))
            if not np.allclose(o,oo) or not np.allclose(v,vv) or not values_ok:
                raise ValueError(f'{file} 与空穴/电子不一致')
        if n==64:
            z=int(np.argmin(abs((o[2]+np.arange(n)*v[2,2])*B2A-3.5)))
            axcoord=(o[0]+np.arange(n)*v[0,0])*B2A
            shared_limit=max(h[:,:,z].max(),e[:,:,z].max())
            for axis,field,title in zip(axes,[h,e,e-h],['Hole','Electron','Electron − hole']):
                plane=field[:,:,z];slices[title]=plane
                limit=np.max(abs(plane)) if '−' in title else shared_limit
                img=axis.pcolormesh(axcoord,axcoord,plane.T,cmap='RdBu_r' if '−' in title else 'viridis',
                                    vmin=-limit if '−' in title else 0,vmax=limit,shading='nearest')
                axis.set(title=title,xlabel='x (Å)',ylabel='y (Å)',aspect='equal')
                fig.colorbar(img,ax=axis,label='Density (a.u.)',shrink=.7)
                axis.scatter(atoms[:,2]*B2A,atoms[:,3]*B2A,c=np.where(atoms[:,0]==8,'red','white'),edgecolors='black',s=20)
            fig.suptitle(f'Periodic water dimer, state 3; z = {(o[2]+z*v[2,2])*B2A:.3f} Å; 64³ cell grid')
    fig.savefig(out/'hole-electron-fields.png',dpi=170);plt.close(fig)
    # 从独立导出的 MO 重建网格，分别计算全矩阵和原生交叉项截断。
    phi=np.array([cube(work/'orbitals-32'/f'orb{i:06d}.cub')[0].ravel() for i in range(1,47)])
    full_h=x@x.T;full_e=x.T@x
    kept=np.where(abs(x)>=.01*np.sqrt(2),x,0)
    cut_h=kept@kept.T;cut_e=kept.T@kept
    np.fill_diagonal(cut_h,np.diag(full_h));np.fill_diagonal(cut_e,np.diag(full_e))
    recon = {}
    for name,mo,q,qfull in [('hole',phi[:8],cut_h,full_h),('electron',phi[8:],cut_e,full_e)]:
        field=np.sum(mo*(q@mo),axis=0)
        exact=np.sum(mo*(qfull@mo),axis=0)
        native=cube(work/'hole-32'/(name+'.cub'))[0].ravel()
        cross=cube(work/'cross-32'/(name+'.cub'))[0].ravel()
        local=np.sum(mo*mo*np.diag(q)[:,None],axis=0)
        error=float(np.max(abs(np.maximum(field,0)-native)))
        cross_error=float(np.max(abs(field-local-cross)))
        if error>1.3e-6 or cross_error>1.3e-6:
            raise ValueError('原生阈值下的 MO 密度重建失败')
        recon[name]=dict(native_max_difference=error,cross_max_difference=cross_error,
                         full_vs_native_threshold_max_difference=float(np.max(abs(exact-field))),
                         unrounded_field_minimum=float(field.min()))
    # 轨道旋转保持完整矩阵的密度；NTO 权重按文件值核对。
    nto_errors={}
    for state in states:
        k=state['state'];values=np.array([float(v) for v in re.findall(r'^Energy=\s*(\S+)',(work/f'nto-{k}/nto.mwfn').read_text(),re.M)])
        err=float(np.max(abs(values[8:16]-state['nto_weights'])))
        if err>2e-8:raise ValueError('NTO 与完整幅度的 SVD 不符')
        nto_errors[k]=err
    c,s,occ,_=ao.mwfn(work/'matrices/matrices.mwfn')
    raw=(work/'matrices/matrices.mwfn').read_text()
    centres=np.fromstring(raw.split('$Shell centers')[1].split('$')[0],sep=' ',dtype=int)
    types=np.fromstring(raw.split('$Shell types')[1].split('$')[0],sep=' ',dtype=int)
    owner=np.repeat(centres,[2*abs(t)+1 if t<0 else (t+1)*(t+2)//2 for t in types])
    if not np.array_equal(occ,[2]*8+[0]*38):raise ValueError('占据数错误')
    fragments=[np.arange(3),np.arange(3,6)]
    atom_h,atom_e=native_atomic_mulliken(x,c,s,owner,.001)
    predicted=np.outer(atom_h,atom_e)
    native_atom=ao.matrix(work/'ifct-mulliken/atmCTmat.txt',6)
    matrix_error=float(np.max(abs(predicted-native_atom)))
    if matrix_error>1e-8:raise ValueError('IFCT 原生原子矩阵未复现')
    uncut_h,uncut_e=native_atomic_mulliken(x,c,s,owner,0)
    fragment_data={}
    fig,axes=plt.subplots(1,2,figsize=(7,3.6),constrained_layout=True)
    saved={}
    for axis,method in zip(axes,['mulliken','hirshfeld']):
        atom=ao.matrix(work/('ifct-'+method)/'atmCTmat.txt',6)
        q=np.array([[atom[np.ix_(a,b)].sum() for b in fragments] for a in fragments])
        hole=q.sum(axis=1);ele=q.sum(axis=0)
        if abs(q.sum()-1)>1e-7 or np.min(atom)<0 or np.linalg.matrix_rank(atom,tol=1e-7)!=1:
            raise ValueError('当前模型的 IFCT 矩阵归一化/秩检查失败')
        fragment_data[method]=dict(hole=hole.tolist(),electron=ele.tolist(),matrix=q.tolist(),
                net_population=(ele-hole).tolist(),CT=float(q.sum()-np.trace(q)),LE=float(np.trace(q)))
        saved[method+'_IFCT']=q
        axis.imshow(q,vmin=0,vmax=1,cmap='Blues')
        for i in range(2):
            for j in range(2):axis.text(j,i,f'{q[i,j]:.4f}',ha='center',va='center',color='white' if q[i,j]>.6 else 'black')
        axis.set(title=method.capitalize(),xlabel='Electron / destination',ylabel='Hole / source',xticks=[0,1],yticks=[0,1],xticklabels=['Water A','Water B'],yticklabels=['Water A','Water B'])
    fig.suptitle('State 3: IFCT from fragment marginals (sum = 1)')
    fig.savefig(out/'ifct-matrices.png',dpi=170);plt.close(fig)
    report=dict(model='Own fixed periodic water dimer, 8 Angstrom cubic cell, Gamma PBE/DZVP-MOLOPT-SR-GTH',
        software=dict(cp2k='2026.2 response reused',multiwfn='2026.7.15'),
        response_sha256=hashlib.sha256(response_file.read_bytes()).hexdigest(),
        wavefunction_sha256=hashlib.sha256((work/'hole-32/periodic.molden').read_bytes()).hexdigest(),
        state=3,convergence=convergence,MO_grid_reconstruction=recon,native_NTO_errors=nto_errors,
        atomic_Mulliken_IFCT_max_difference=matrix_error,fragments=fragment_data,
        full_Mulliken_net_population_A=float(uncut_e[:3].sum()-uncut_h[:3].sum()),
        native_threshold_Mulliken_net_population_A=float(atom_e[:3].sum()-atom_h[:3].sum()),
        plotting=dict(slice_z_angstrom=float((o[2]+z*v[2,2])*B2A),density_unit='electron/bohr^3',
                      atom_positions='xy projection',hole_electron_share_colour_scale=True),
        notes=['Native grid cross term discards coefficients below .01; native Mulliken coefficient-product cutoff .001 and normalization reproduced',
               'Periodic centroids and widths refer to this chosen cell; no exciton radius/binding energy or dynamics inferred',
               'Default periodic image range retained; the grid comparison is not a basis/image-range convergence proof'])
    (out/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'analysis.npz',slice_xy_angstrom=axcoord,
                        slice_z_angstrom=(o[2]+z*v[2,2])*B2A,
                        **slices,**saved,**{f'transition_{k}':v for k,v in matrices.items()})
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root',type=Path,required=True)
    parser.add_argument('--response',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();main(args.work_root,args.response,args.output_dir)
