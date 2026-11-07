"""从固定水二聚体的原生输出重建轨道分区、DOS和CDA。

从仓库根目录调用：python examples/orca/minimal/orbital-dos-cda/analyze.py \
  --work-root WORK --output-dir OUT
需要numpy。限定实数闭壳层、完整48/24/24轨道与本例原子顺序；能量Ha，坐标Å。
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np

EV = 27.2113838  # 对应本例Multiwfn版本的换算常数


def mwfn(path):
    raw = path.read_text()
    n = int(re.search(r'Nbasis=\s*(\d+)', raw)[1])
    body = raw.split('$Overlap matrix', 1)[1].split('\n', 1)[1].split('$', 1)[0]
    values = np.fromstring(body, sep=' ')
    if values.size != n*(n+1)//2:
        raise ValueError('重叠矩阵下三角长度不符')
    s = np.zeros((n, n)); pos = np.tril_indices(n)
    s[pos] = values; s[(pos[1], pos[0])] = values
    blocks = re.split(r'(?m)^Index=', raw.split('$Total density matrix')[0])[1:]
    coeff, occ, energy = [], [], []
    for block in blocks:
        coeff.append(np.fromstring(block.split('$Coeff', 1)[1].split('#', 1)[0], sep=' '))
        occ.append(float(re.search(r'Occ=\s*([\d.E+-]+)', block)[1]))
        energy.append(float(re.search(r'Energy=\s*([\d.E+-]+)', block)[1]))
    c = np.array(coeff).T
    if c.shape != (n, n) or np.max(abs(c.T@s@c-np.eye(n))) > 2e-6:
        raise ValueError('本例要求完整且S正交归一的轨道空间')
    return c, s, np.array(occ), np.array(energy)


def matrix(path, n):
    result = np.full((n, n), np.nan)
    columns = []
    for line in path.read_text().splitlines():
        tokens = line.split()
        if not tokens: continue
        if all(re.fullmatch(r'\d+', t) for t in tokens):
            columns = [int(t)-1 for t in tokens]
        elif columns and re.fullmatch(r'\d+', tokens[0]) and len(tokens) == len(columns)+1:
            result[int(tokens[0])-1, columns] = [float(t) for t in tokens[1:]]
    if not np.isfinite(result).all(): raise ValueError('分块矩阵未读完整')
    return result


def gaussian(energy, levels, fwhm):
    sigma = fwhm/np.sqrt(8*np.log(2))
    return np.exp(-.5*((energy[:, None]-levels)/sigma)**2)/(np.sqrt(2*np.pi)*sigma)


def fortran_number(token):
    if isinstance(token, bytes): token=token.decode()
    # Fortran固定宽度在三位指数时可能省略E，例如4.940656-324；保留其数值。
    token=re.sub(r'(?<=\d)([+-]\d{3})$', r'E\1', token) if 'e' not in token.lower() else token
    return float(token.replace('D','E'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(); root=args.work_root
    c,s,occ,_ = mwfn(root/'composition/complex.mwfn')
    if c.shape != (48,48) or not np.array_equal(occ, [2]*10+[0]*38):
        raise ValueError('本例应有48个空间轨道和20电子')
    energy = np.array([float(v) for v in re.findall(r'Ene=\s*([\d.E+-]+)', (root/'complex.molden.input').read_text())])
    if energy.shape != (48,): raise ValueError('能级数量不符')
    ca,sa,oa,ea=mwfn(root/'fragment-1/fragment.mwfn')
    cb,sb,ob,eb=mwfn(root/'fragment-2/fragment.mwfn')
    if ca.shape != (24,24) or cb.shape != (24,24) or oa.sum()!=10 or ob.sum()!=10:
        raise ValueError('片段空间或电子数不符')
    mull=(c*(s@c))[:24].sum(axis=0)
    scpa=(c*c)[:24].sum(axis=0)/(c*c).sum(axis=0)
    overlap=2*np.einsum('mi,mn,ni->i',c[:24],s[:24,24:],c[24:])
    norm=np.einsum('mi,mn,ni->i',c,s,c)
    if np.max(abs(norm-1))>2e-6: raise ValueError('归一化不符')
    f=np.zeros_like(c);f[:24,:24]=ca;f[24:,24:]=cb
    co=np.linalg.solve(f,c); sf=f.T@s@f
    # 原生CDA将同片段S正交关系设为理想块；跨片段仍使用实际重叠。
    sf[:24,:24]=np.eye(24);sf[24:,24:]=np.eye(24)
    native_co=matrix(root/'cda/coFO.txt',48); native_sf=matrix(root/'cda/ovlpint.txt',48)
    coerr=float(np.max(abs(co-native_co)));serr=float(np.max(abs(sf-native_sf)))
    if coerr>3e-7 or serr>3e-7: raise ValueError('独立AO→FO变换与原生输出不符')
    pair=occ[None,None,:]*co[:24,None,:]*co[None,24:,:]*sf[:24,24:,None]
    fac=(oa[:,None]-ob[None,:])/2
    d=(pair*np.maximum(fac,0)[:,:,None]).sum(axis=(0,1))
    b=(pair*np.maximum(-fac,0)[:,:,None]).sum(axis=(0,1))
    rep=(pair*(2*np.minimum(oa[:,None],ob[None,:])/2)[:,:,None]).sum(axis=(0,1))
    log=(root/'cda/run.log').read_text()
    printed=np.fromstring(re.search(r'Sum:\s*([^\n]+)',log)[1],sep=' ')
    terms=np.array([occ.sum(),d.sum(),b.sum(),d.sum()-b.sum(),rep.sum()])
    if not np.allclose(terms,printed,rtol=0,atol=5.1e-7): raise ValueError('CDA总项与原生六位小数不符')
    fo_weight=co*(sf@co)
    ecda=2*(fo_weight[:5,10:].sum()-fo_weight[5:24,:10].sum())
    printed_ecda=float(re.search(r'The net electrons obtained by frag\. 2[^\n]*=\s*([\d.-]+)',log)[1])
    if abs(ecda-printed_ecda)>5.1e-5: raise ValueError('ECDA与原生输出不符')
    curves={}; errors={}; arrays={}
    for job,width in [('dos-002',.02),('dos-005',.05),('dos-ev',.02*EV)]:
        table=np.loadtxt(root/job/'DOS_curve.txt')
        axis=np.linspace(-1.5,1.5,len(table));levels=energy.copy()
        if job=='dos-ev': axis*=EV;levels*=EV
        if np.max(abs(table[:,0]-axis))>5.1e-6: raise ValueError('DOS能量格点与输出精度不符')
        g=gaussian(axis,levels,width)
        expected=np.column_stack([g.sum(axis=1),g@overlap,g@mull,g@(1-mull)])
        error=float(np.max(abs(table[:,1:5]-expected)))
        if error>2e-6: raise ValueError(f'{job}的曲线重建差异{error}')
        if np.max(abs(table[:,1]-table[:,3]-table[:,4]))>1.1e-6: raise ValueError('完备不相交片段PDOS应加和为TDOS')
        errors[job]=error; arrays[job.replace('-','_')]=table[:,:5]
        curves[job]=dict(fwhm=width,energy_unit='eV' if job=='dos-ev' else 'Ha',max_rebuild_difference=error,finite_window_state_integral=float(np.trapezoid(table[:,1],axis)))
    hir=np.loadtxt(root/'dos-hirshfeld/DOS_curve.txt')
    if np.min(hir[:,1:4])<0 or np.max(abs(hir[:,1]-hir[:,2]-hir[:,3]))>1.1e-6:
        raise ValueError('本例Hirshfeld PDOS正性或完备性不符')
    arrays['dos_hirshfeld']=hir[:,:4]
    ldos=np.loadtxt(root/'ldos/LDOS_curve.txt',converters=fortran_number);line=np.loadtxt(root/'ldos/LDOS_line.txt',converters=fortran_number)
    # 竖线每条轨道三行，中间行为概率密度；轨道空间求值由原生程序完成。
    weights=line[1::3,1]
    kernel=gaussian(np.linspace(-1.5,1.5,len(ldos)),energy,.02)
    expected=kernel@weights
    ldoserr=float(np.max(abs(expected-ldos[:,1])))
    def rounding_bound(values):
        bound=np.zeros_like(values);mask=abs(values)>1e-300
        bound[mask]=.50001*10.**(np.floor(np.log10(abs(values[mask])))-6)
        return bound
    # 两份LDOS文件均输出7位有效数字，传播逐轨道权重及曲线本身的舍入界。
    if np.any(abs(expected-ldos[:,1])>kernel@rounding_bound(weights)+rounding_bound(ldos[:,1])+1e-12):
        raise ValueError('LDOS逐轨道权重展宽超出导出舍入误差界')
    arrays['ldos']=ldos;arrays.update(energy_Ha=energy,occupations=occ,mulliken=mull,scpa=scpa,AO_overlap=overlap,cda_d=d,cda_b=b,cda_r=rep,FO_coefficients=co,FO_overlap=sf,FO_energies_Ha=np.concatenate([ea,eb]),FO_compositions=fo_weight)
    data=dict(model='Fixed unoptimized water dimer, O-O2.9A, neutral singlet PBE0/def2-SVP; isolated fragment geometry identical to complex; no ghost centres',software='ORCA6.1.1 and Multiwfn2026.7.15',fragment_A='atoms1-3, FOs1-24',fragment_B='atoms4-6, FOs25-48',basis_count=48,occupied_spatial_orbitals=10,spin_convention='one spatial orbital counts once in DOS; occupations used separately in populations/CDA',full_state_count=48,finite_plot_window_Ha=[-1.5,1.5],mulliken_range=[float(mull.min()),float(mull.max())],scpa_range=[float(scpa.min()),float(scpa.max())],HOMO=dict(index=10,energy_Ha=float(energy[9]),mulliken_fragment_A=float(mull[9]),scpa_fragment_A=float(scpa[9])),LUMO=dict(index=11,energy_Ha=float(energy[10]),mulliken_fragment_A=float(mull[10]),scpa_fragment_A=float(scpa[10])),curves=curves,LDOS=dict(point_Bohr=[2.7,0,0],max_broadening_difference=ldoserr,weight_unit='Bohr^-3'),CDA=dict(d_e=float(d.sum()),b_e=float(b.sum()),d_minus_b_e=float(d.sum()-b.sum()),r_e=float(rep.sum()),ECDA_net_A_to_B_e=float(ecda),normalization='GCDA uses refocc2; r is twice original CDA formula r; signed terms, not probabilities or energies',coefficient_reconstruction_max_error=coerr,overlap_reconstruction_max_error=serr),energy_conversion_eV_per_Ha=EV,public_plot_convention='From Ha curves: convert x byEV and DOS y by1/EV; native eV conversion separately checked with explicit scale ratioEV compensating strength1/EV',source_sha256={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [root/'complex.molden.input',root/'fragment-1/orca.molden.input',root/'fragment-2/orca.molden.input']})
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'orbital-analysis.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(args.output_dir/'orbital-data.npz',**arrays)
    print(json.dumps(dict(CDA=data['CDA'],DOS_errors=errors,LDOS_error=ldoserr),ensure_ascii=False))


if __name__=='__main__':main()
