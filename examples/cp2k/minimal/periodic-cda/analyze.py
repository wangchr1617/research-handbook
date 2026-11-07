"""核对同一8Å周期盒中水二聚体的46=23+23轨道与CDA/ECDA。

python examples/cp2k/minimal/periodic-cda/analyze.py --work-root WORK --output OUTPUT.json
依赖numpy，读取原生MWFN、coFO/ovlpint与CP2K日志，不重算SCF。
"""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import numpy as np

reader=Path(__file__).resolve().parents[3]/'orca/minimal/orbital-dos-cda/analyze.py'
spec=importlib.util.spec_from_file_location('orbital_io',reader)
io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();root=args.work_root
    c,s,o,e=io.mwfn(root/'periodic-cda/complex.mwfn')
    ca,sa,oa,ea=io.mwfn(root/'periodic-A/matrices.mwfn')
    cb,sb,ob,eb=io.mwfn(root/'periodic-B/matrices.mwfn')
    if c.shape!=(46,46) or ca.shape!=(23,23) or cb.shape!=(23,23) or (o.sum(),oa.sum(),ob.sum())!=(16,8,8):
        raise ValueError('本例需完整46=23+23轨道及16=8+8价电子')
    if not np.allclose(s[:23,:23],sa,rtol=0,atol=1e-8) or not np.allclose(s[23:,23:],sb,rtol=0,atol=1e-8):
        raise ValueError('相同坐标、晶胞、基组的片段重叠块不匹配')
    f=np.zeros_like(c);f[:23,:23]=ca;f[23:,23:]=cb
    co=np.linalg.solve(f,c);sf=f.T@s@f
    sf[:23,:23]=np.eye(23);sf[23:,23:]=np.eye(23)
    native_co=io.matrix(root/'periodic-cda/coFO.txt',46);native_sf=io.matrix(root/'periodic-cda/ovlpint.txt',46)
    coerror=float(np.max(abs(co-native_co)));serror=float(np.max(abs(sf-native_sf)))
    if max(coerror,serror)>3e-7:raise ValueError('周期AO→FO矩阵与原生不符')
    pair=o[None,None,:]*co[:23,None,:]*co[None,23:,:]*sf[:23,23:,None]
    fac=(oa[:,None]-ob[None,:])/2
    d=(pair*np.maximum(fac,0)[:,:,None]).sum((0,1));b=(pair*np.maximum(-fac,0)[:,:,None]).sum((0,1))
    rep=(pair*np.minimum(oa[:,None],ob[None,:])[:,:,None]).sum((0,1))
    log=(root/'periodic-cda/run.log').read_text();native=np.fromstring(re.search(r'Sum:\s*([^\n]+)',log)[1],sep=' ')
    terms=[o.sum(),d.sum(),b.sum(),d.sum()-b.sum(),rep.sum()]
    if not np.allclose(terms,native,rtol=0,atol=5.1e-7):raise ValueError('原生CDA总项不符')
    weights=co*(sf@co);ecda=2*(weights[:4,8:].sum()-weights[4:23,:8].sum())
    native_ecda=float(re.search(r'The net electrons obtained by frag\. 2[^\n]*=\s*([-\d.]+)',log)[1])
    mull_B=np.sum((c*(s@c))[23:]*o)
    if abs(ecda-native_ecda)>5.1e-5 or abs(ecda-(mull_B-8))>1e-6:
        raise ValueError('ECDA与当前同AO分块的Mulliken净布居不一致')
    cp=[]
    for tag in ['complex','A','B']:
        path=root/f'periodic-{tag}';text=(path/'cp2k.out').read_text()
        if 'SCF run converged' not in text:raise ValueError('需检查实际SCF收敛')
        molden=(path/'periodic-MOS-1_0.molden').read_text()
        cell=np.array([list(map(float,line.split())) for line in molden.split('[Cell] Angs')[1].strip().splitlines()[:3]])
        if not np.array_equal(cell,np.eye(3)*8):raise ValueError('晶胞或单位不符')
        cp.append(dict(fragment=tag,energy_Ha=float(re.search(r'ENERGY\| Total FORCE_EVAL.*?([-\d.]+)\s*$',text,re.M)[1]),SCF_steps=int(re.search(r'SCF run converged in\s+(\d+)',text)[1]),wavefunction_sha256=hashlib.sha256((path/'periodic-MOS-1_0.molden').read_bytes()).hexdigest()))
    data=dict(model='Fixed water dimer in8A cubic periodic box; PBE/DZVP-MOLOPT-SR-GTH, Oq6/Hq1, Gamma only; no adsorption slab or phase inference',software='CP2K2026.2 and Multiwfn2026.7.15',cell_A=[8,8,8],basis_counts=[46,23,23],explicit_electrons=[16,8,8],full_orbital_space=True,reference_fragments='neutral singlet Aatoms1-3, Batoms4-6 at same cell/coordinates/basis; no ghost centres',CDA=dict(d_e=float(d.sum()),b_e=float(b.sum()),d_minus_b_e=float(d.sum()-b.sum()),r_e=float(rep.sum()),per_orbital=[dict(index=i+1,d_e=float(d[i]),b_e=float(b[i]),r_e=float(rep[i])) for i in range(46)]),ECDA_net_A_to_B_e=float(ecda),Mulliken_B_electrons=float(mull_B),Mulliken_B_net_charge_e=float(8-mull_B),coefficient_max_difference=coerror,overlap_max_difference=serror,overlap_condition_number=float(np.linalg.cond(s)),SCF=cp,conventions='Mulliken/ECDA agreement here follows same complete AO block partition and integer occupations; not universal agreement with Hirshfeld/Bader/other charge definitions')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CDA=terms,ECDA=float(ecda),Mulliken_change=float(mull_B-8),coefficient_error=coerror),ensure_ascii=False))


if __name__=='__main__':main()
