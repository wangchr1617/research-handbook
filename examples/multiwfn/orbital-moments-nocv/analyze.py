"""核对孤立Zn的D投影质心和固定水二聚体的NOCV密度分解。

python examples/multiwfn/orbital-moments-nocv/analyze.py --work-root WORK --output-dir OUT
依赖numpy/scipy；复用本仓库MWFN和正交Cube读取器。Zn不是表面催化模型。
"""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import numpy as np
from scipy.special import ndtr


def helper(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


EXAMPLES=Path(__file__).resolve().parents[2]
orb=helper('orbital_io',EXAMPLES/'orca/minimal/orbital-dos-cda/analyze.py')
field=helper('cube_io',EXAMPLES/'orca/minimal/weak-interactions/analyze.py')


def truncated_gaussian_moment(energies,weights,width,low,high):
    sigma=width/np.sqrt(8*np.log(2))
    za,zb=(low-energies)/sigma,(high-energies)/sigma
    mass=ndtr(zb)-ndtr(za)
    first=energies*mass+sigma*(np.exp(-za*za/2)-np.exp(-zb*zb/2))/np.sqrt(2*np.pi)
    denominator=weights@mass
    if denominator<=1e-12:raise ValueError('所选窗口没有足够的投影权重')
    return float(weights@first/denominator),float(denominator)


def analyze(root,out):
    zc,zs,zo,ze=orb.mwfn(root/'zn/matrices.mwfn')
    raw=(root/'zn/matrices.mwfn').read_text()
    types=np.fromstring(raw.split('$Shell types')[1].split('$')[0],sep=' ',dtype=int)
    sizes=[2*abs(t)+1 if t<0 else (t+1)*(t+2)//2 for t in types]
    mask=np.concatenate([np.repeat(abs(t)==2,n) for t,n in zip(types,sizes)])
    weights=(zc*(zs@zc))[mask].sum(axis=0)
    if mask.sum()!=10 or zo.sum()!=30:raise ValueError('本例应有10个Zn D基函数和30电子')
    # 原始Molden能级比MWFN导出保留更多有效数字，用于逐点重建窄峰。
    energies=np.array([float(x) for x in re.findall(r'Ene=\s*([\d.E+-]+)',(root/'zn/orca.molden.input').read_text())])
    moments={};arrays={}
    definitions=[('zn-dos-narrow',.02,-1,.8),('zn-dos-wide',.1,-1,.8),('zn-dos-short-narrow',.02,-.4,-.3),('zn-dos-short',.1,-.4,-.3)]
    for name,width,low,high in definitions:
        table=np.loadtxt(root/name/'DOS_curve.txt');x=np.linspace(low,high,len(table))
        kernel=orb.gaussian(x,energies,width);expected=kernel@weights
        if table.shape[1]!=12 or np.max(abs(table[:,2]-expected))>2e-6:raise ValueError('Zn D-PDOS与独立基函数选择/展宽不符')
        if np.max(abs(table[:,0]-x))>5.1e-6:raise ValueError('原生能量网格不符')
        centre=float(np.sum(x*expected)/expected.sum())
        printed=float(re.search(r'Center of PDOS\s+1:\s*([-\d.]+)',(root/name/'run.log').read_text())[1])
        if abs(centre-printed)>5.1e-7:raise ValueError('原生矩形求和质心不符')
        analytic,mass=truncated_gaussian_moment(energies,weights,width,low,high)
        moments[name]=dict(window_Ha=[low,high],FWHM_Ha=width,native_rectangle_centre_Ha=printed,continuous_centre_Ha=analytic,window_projected_mass=mass)
        arrays[name.replace('-','_')]=table[:,:3]
    homoid=np.where(zo>0)[0][-1];homo=float(energies[homoid])
    c,s,occ,ene=orb.mwfn(root/'complex-matrices.mwfn')
    ca,_,oa,_=orb.mwfn(root/'fragment-1-matrices.mwfn')
    cb,_,ob,_=orb.mwfn(root/'fragment-2-matrices.mwfn')
    f=np.zeros_like(c);f[:24,:24]=ca;f[24:,24:]=cb
    fo_occ=np.concatenate([oa,ob]);u=f[:,fo_occ>0]
    gram=u.T@s@u
    val,vec=np.linalg.eigh(gram)
    if val.min()<=1e-8:raise ValueError('片段占据空间病态，不能稳定定义本例冻结态')
    frozen=u@(vec/np.sqrt(val))@vec.T
    pfrz=2*frozen@frozen.T
    ppro=(f*fo_occ)@f.T;pactual=(c*occ)@c.T
    delta=pactual-pfrz
    eigs,q=np.linalg.eigh(s)
    shalf=(q*np.sqrt(eigs))@q.T
    calculated=np.linalg.eigvalsh(shalf@delta@shalf)[::-1]
    nc,ns,nu,ne=orb.mwfn(root/'nocv/NOCV.mwfn')
    if np.max(abs(nu-calculated))>2e-7:raise ValueError('度量变换后的密度差谱与原生NOCV不符')
    reconstruction=(nc*nu)@nc.T
    matrix_error=float(np.max(abs(reconstruction-delta)))
    if matrix_error>2e-7:raise ValueError('NOCV重建密度差不符')
    original_energies=np.array([float(x) for x in re.findall(r'Ene=\s*([\d.E+-]+)',(root/'complex.molden.input').read_text())])
    final_fock=s@c@np.diag(original_energies)@np.linalg.inv(c)
    nv_energy=np.einsum('mi,mn,ni->i',nc,final_fock,nc)
    if np.max(abs(ne-nv_energy))>2e-7:raise ValueError('最终态Fock近似的轨道期望值不符')
    pair_energy=(nu[:24]*nv_energy[:24]+nu[::-1][:24]*nv_energy[::-1][:24])*627.51
    approx=float(np.sum(pair_energy));trace_energy=float(np.sum(delta*final_fock.T)*627.51)
    energy_bound=float(np.linalg.norm(reconstruction-delta)*np.linalg.norm(final_fock)*627.51)
    if abs(approx-trace_energy)>energy_bound+1e-8:raise ValueError('pair总和与Tr(deltaP F_final)超出矩阵重建误差界')
    grids={};origin=vectors=atoms=None
    for key,name in [('pair1','pair-1.cub'),('all_pairs','all-pairs.cub'),('pauli','Pauli.cub'),('orbital','orb_def.cub'),('total','EDD.cub')]:
        data,o,v,a=field.cube(root/'nocv'/name)
        if origin is not None and (data.shape!=grids['pair1'].shape or not all(np.array_equal(x,y) for x,y in [(o,origin),(v,vectors),(a,atoms)])):
            raise ValueError('密度差网格或坐标不一致')
        if not np.isfinite(data).all():raise ValueError('非有限密度差')
        grids[key]=data;origin,vectors,atoms=o,v,a
    def cube_error_bound(a):
        limit=np.zeros_like(a);positive=abs(a)>1e-290
        limit[positive]=.5001*10.**(np.floor(np.log10(abs(a[positive])))-5)
        return limit
    additive=grids['pauli']+grids['orbital']-grids['total']
    bound=sum(cube_error_bound(grids[k]) for k in ['pauli','orbital','total'])+1e-13
    if np.any(abs(additive)>bound):raise ValueError('Pauli+轨道密度差与总密度差超出导出舍入界')
    error=grids['all_pairs']-grids['orbital']
    if np.max(abs(error))>1e-7:raise ValueError('全pair网格与轨道密度差不符')
    index=int(np.argmin(abs(origin[2]+np.arange(grids['pair1'].shape[2])*vectors[2,2])))
    arrays.update(zn_energy_Ha=energies,zn_D_weights=weights,NOCV_eigenvalues=nu,NOCV_energy_expectations_Ha=nv_energy,NOCV_pair_energies_kcal=pair_energy,NOCV_coefficients=nc,deltaP_orb=delta,deltaP_pauli=pfrz-ppro,deltaP_total=pactual-ppro,origin_Bohr=origin,vectors_Bohr=vectors,z_index=index)
    for key,a in grids.items():arrays[key]=a[:,:,index]
    info=dict(Zn=dict(model='Isolated neutral Zn, PBE/def2-SVP, closed shell; D-subspace moment check, not surface catalysis',D_basis_functions=int(mask.sum()),HOMO_Ha=homo,moments=moments,finite_window_FWHM_shift_Ha=moments['zn-dos-short']['native_rectangle_centre_Ha']-moments['zn-dos-short-narrow']['native_rectangle_centre_Ha']),NOCV=dict(model='Fixed water dimer and neutral singlet fragments PBE0/def2-SVP',reference='Loewdin-orthogonalized occupied fragment orbitals',positive_eigenvalues=nu[:10].tolist(),pair_energies_kcal_mol=pair_energy[:10].tolist(),approximate_energy_sum_kcal_mol=approx,trace_energy_kcal_mol=trace_energy,energy_trace_reconstruction_bound_kcal_mol=energy_bound,energy_operator='Final-state Fock/KS expectation; not ETS midpoint operator or full EDA energy',density_matrix_reconstruction_max_error=matrix_error,trace_deltaP_S=float(np.trace(delta@s)),smallest_fragment_occupied_gram_eigenvalue=float(val.min()),metric_spectrum_max_difference=float(np.max(abs(nu-calculated))),cube_sum_max_residual=float(np.max(abs(additive))),all_pair_orbital_cube_max_difference=float(np.max(abs(error))),z_slice_A=float((origin[2]+index*vectors[2,2])*field.BOHR_A),grid_shape=list(grids['pair1'].shape)),software='ORCA6.1.1, Multiwfn2026.7.15',source_sha256={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [root/'zn/orca.molden.input',root/'complex.molden.input',root/'fragment-1.molden.input',root/'fragment-2.molden.input']})
    out.mkdir(parents=True,exist_ok=True)
    (out/'moments-nocv.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'moments-nocv.npz',**arrays)
    print(json.dumps(dict(Zn_width_shift_Ha=info['Zn']['finite_window_FWHM_shift_Ha'],NOCV=info['NOCV']),ensure_ascii=False))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args();analyze(args.work_root,args.output_dir)


if __name__=='__main__':main()
