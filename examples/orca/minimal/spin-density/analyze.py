"""核对UHF密度、UNO/NSO/SNO和自旋网格；python analyze.py --work-root WORK --output-dir OUT。"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def mwfn(path):
    raw=path.read_text();n=int(re.search(r'Nbasis=\s*(\d+)',raw)[1]);blocks=re.split(r'(?m)^Index=',raw.split('# Various matrices')[0])[1:]
    c=np.array([np.fromstring(b.split('$Coeff')[1].split('#')[0],sep=' ') for b in blocks]).T
    occ=np.array([float(re.search(r'Occ=\s*([-+\d.Ee]+)',b)[1]) for b in blocks]);types=np.array([int(re.search(r'Type=\s*(\d+)',b)[1]) for b in blocks])
    if c.shape[0]!=n or not np.isfinite(c).all() or not np.isfinite(occ).all():raise ValueError('轨道文件不完整')
    return c,occ,types,raw


def matrix(raw,label,n):
    body=raw.split('$'+label+',')[1].split('\n',1)[1].split('$')[0];values=np.fromstring(body,sep=' ')
    if len(values)!=n*(n+1)//2:raise ValueError('三角矩阵长度不符')
    a=np.zeros((n,n));idx=np.tril_indices(n);a[idx]=values;a[(idx[1],idx[0])]=values;return a


def metric(s):
    e,u=np.linalg.eigh(s)
    if e.min()<=1e-10:raise ValueError('基组度量近线性相关')
    return (u*np.sqrt(e))@u.T,(u/np.sqrt(e))@u.T


def cube(path):
    lines=path.read_text().splitlines();nat=int(lines[2].split()[0]);shape=[int(lines[k].split()[0]) for k in [3,4,5]];origin=np.array(lines[2].split()[1:4],float);v=np.array([lines[k].split()[1:4] for k in [3,4,5]],float)
    values=np.fromstring(' '.join(lines[6+nat:]),sep=' ')
    if nat!=2 or min(shape)<=0 or len(values)!=np.prod(shape) or np.max(abs(v-np.diag(np.diag(v))))>1e-12 or np.any(np.diag(v)<=0):raise ValueError('需要本例正交单标量H2网格')
    return values.reshape(shape),origin,v


def polarization(m,rho,minimum_density=1e-8):
    m,rho=np.asarray(m),np.asarray(rho)
    if m.shape!=rho.shape or not np.isfinite(m).all() or not np.isfinite(rho).all() or minimum_density<=0:raise ValueError('无效自旋/总密度')
    valid=rho>minimum_density;zeta=np.full(rho.shape,np.nan);zeta[valid]=m[valid]/rho[valid]
    if np.max(abs(zeta[valid]))>1.00003:raise ValueError('自旋极化比超出物理范围及打印误差')
    return zeta,valid


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();root,out=a.work_root,a.output_dir;out.mkdir(parents=True,exist_ok=True)
    result={'model':'Own H2 at2.4Angstrom, RHF/UHF def2-SVP VeryTightSCF, ORCA6.1.1/Multiwfn2026.7.15','methods':{},'source_sha256':{},'scope':'BS has Ms0 but is not a pure singlet; no projected ground-state or experimental magnetic moment inferred.'};saved={};profiles={}
    for mode in ['rhf','hs','bs']:
        log=(root/mode/'orca.out').read_text()
        if 'ORCA TERMINATED NORMALLY' not in log:raise ValueError('SCF未正常结束')
        energy=float(re.findall(r'FINAL SINGLE POINT ENERGY\s+([-\d.]+)',log)[-1]);spin2=re.findall(r'Expectation value of <S\*\*2>\s*:\s*([-\d.]+)',log)
        c,occ,types,raw=mwfn(root/f'{mode}-export/matrices.mwfn');n=c.shape[0]
        if n!=10:raise ValueError('本例需要10基函数')
        s=matrix(raw,'Overlap matrix',n);half,inv=metric(s)
        if mode=='rhf':pa=pb=matrix(raw,'Total density matrix',n)/2;ca=cb=c[:,:1]
        else:
            pa=matrix(raw,'Alpha density matrix',n);pb=matrix(raw,'Beta density matrix',n)
            ca=c[:,types==1][:,occ[types==1]>.5];cb=c[:,types==2][:,occ[types==2]>.5]
        if np.max(abs(pa-ca@ca.T))>1e-7 or np.max(abs(pb-cb@cb.T))>1e-7:raise ValueError('矩阵与占据轨道不对应')
        total,spin=pa+pb,pa-pb;no=np.linalg.eigvalsh(half@total@half)[::-1];sno=np.linalg.eigvalsh(half@spin@half)[::-1]
        na,nb=np.trace(pa@s),np.trace(pb@s);ms=(na-nb)/2;expected_s2=ms*(ms+1)+nb-np.sum((ca.T@s@cb)**2)
        if mode!='rhf' and abs(expected_s2-float(spin2[-1]))>6e-7:raise ValueError('独立S2不对应原生输出')
        mull_basis=np.diag(spin@s);mull=np.array([mull_basis[:5].sum(),mull_basis[5:].sum()])
        item={'energy_Ha':energy,'Nalpha':float(na),'Nbeta':float(nb),'Ms':float(ms),'S2_from_orbitals':float(expected_s2),'native_printed_S2':0 if mode=='rhf' else float(spin2[-1]),'Mulliken_atom_spin':mull.tolist(),'UNO_occupations':no.tolist(),'SNO_eigenvalues':sno.tolist(),'NO_odd_weight_sum':float(np.minimum(no,2-no).sum())}
        if mode!='rhf':
            errors={}
            for kind,target in [('UNO',total),('SNO',spin)]:
                cn,nn,tt,_=mwfn(root/f'{mode}-{kind}/new.mwfn')
                # Current SNO export is one spatial set with signed weights.
                reconstructed=(cn*nn)@cn.T;errors[kind]=float(np.max(abs(reconstructed-target)))
                if errors[kind]>1e-7:raise ValueError('原生NO/SNO重建不符')
                saved[f'{mode}_{kind}_native_weights']=nn
            cn,nn,tt,_=mwfn(root/f'{mode}-NSO/new.mwfn')
            for channel,tgt in [(1,pa),(2,pb)]:
                cc=cn[:,tt==channel];oo=nn[tt==channel];error=float(np.max(abs((cc*oo)@cc.T-tgt)));errors[f'NSO{channel}']=error
                if error>1e-7:raise ValueError('NSO通道重建不符')
            text=(root/f'{mode}-becke/multiwfn.out').read_text();becke=[float(v) for v in re.findall(r'^\s*\d+\(H\s*\)\s+([-\d.]+)',text,re.M)]
            if len(becke)!=2 or abs(sum(becke)-(na-nb))>2e-5:raise ValueError('Becke空间积分不符')
            # Parse the final population table; the BS output contains both HS and BS stages.
            table=log.rsplit('MULLIKEN ATOMIC CHARGES AND SPIN POPULATIONS',1)[1].split('Sum of atomic charges')[0]
            native_mull=[float(row[1]) for row in re.findall(r'^\s*\d+\s+H\s*:\s*([-\d.]+)\s+([-\d.]+)',table,re.M)]
            if len(native_mull)!=2 or np.max(abs(mull-native_mull))>6e-7:raise ValueError('ORCA自旋布居不符')
            spin_grid,origin,v=cube(root/f'{mode}-spin-grid/spindensity.cub');rho,origin2,v2=cube(root/f'{mode}-rho-grid/density.cub')
            if spin_grid.shape!=rho.shape or not np.array_equal(origin,origin2) or not np.array_equal(v,v2):raise ValueError('自旋与总密度网格不匹配')
            zeta,valid=polarization(spin_grid,rho);step=np.diag(v);volume=np.linalg.det(v);x=(origin[0]+np.arange(len(spin_grid))*step[0])*.529177210903
            line=spin_grid.sum(axis=(1,2))*step[1]*step[2];jy=int(np.argmin(abs(origin[1]+np.arange(rho.shape[1])*step[1])));kz=int(np.argmin(abs(origin[2]+np.arange(rho.shape[2])*step[2])))
            profiles[mode]=(x,line,zeta[:,jy,kz])
            item.update(native_NO_reconstruction_AO_max_differences=errors,Becke_atom_spin=becke,spin_grid_integral=float(spin_grid.sum()*volume),spin_grid_absolute_integral=float(abs(spin_grid).sum()*volume),rho_grid_integral=float(rho.sum()*volume),zeta_density_mask=1e-8,zeta_max_absolute_valid=float(np.max(abs(zeta[valid]))))
        result['methods'][mode]=item
        for name,value in [('S',s),('Palpha',pa),('Pbeta',pb),('UNO',no),('SNO',sno)]:saved[f'{mode}_{name}']=value
        files=[f'{mode}/orca.inp',f'{mode}/structure.xyz',f'{mode}/orca.out',f'{mode}/orca.molden.input',f'{mode}-export/matrices.mwfn',f'{mode}-export/scf.fch']
        if mode!='rhf':files += [f'{mode}-{kind}/new.mwfn' for kind in ['UNO','NSO','SNO']]+[f'{mode}-{kind}/multiwfn.out' for kind in ['UNO','NSO','SNO','becke','spin-grid','rho-grid']]
        if mode!='rhf':files += [f'{mode}-spin-grid/spindensity.cub',f'{mode}-rho-grid/density.cub']
        for name in files:result['source_sha256'][name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
    fig,axes=plt.subplots(1,2,figsize=(9,3.8),layout='constrained')
    for mode,label in [('hs','UHF high-spin, Ms=1'),('bs','UHF broken symmetry, Ms=0')]:
        x,line,zeta=profiles[mode];axes[0].plot(x,line,label=label);axes[1].plot(x,zeta,label=label)
        saved[f'{mode}_x_Angstrom']=x;saved[f'{mode}_spin_yz_integrated_bohr1']=line;saved[f'{mode}_zeta_bond_axis']=zeta
    axes[0].set(ylabel='yz-integrated spin density (bohr^-1)',title='Signed spin density');axes[1].set(ylabel='Spin polarization ratio on bond axis',title='zeta = spin density / electron density',ylim=(-1.1,1.1))
    for ax in axes:
        ax.axhline(0,c='#aaa',lw=.6);ax.axvline(-1.2,c='#aaa',ls=':',lw=.6);ax.axvline(1.2,c='#aaa',ls=':',lw=.6);ax.set_xlabel('x (Angstrom)');ax.legend(fontsize=7)
    fig.suptitle('H2 at2.4Angstrom; UHF/def2-SVP; zeta masked below rho=1e-8bohr^-3',fontsize=9)
    fig.savefig(out/'spin-density-and-polarization.png',dpi=180);plt.close(fig)
    (out/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');np.savez_compressed(out/'analysis.npz',**saved)
    print(json.dumps({m:{k:result['methods'][m][k] for k in ['energy_Ha','Ms','S2_from_orbitals','NO_odd_weight_sum']} for m in ['rhf','hs','bs']},ensure_ascii=False))


if __name__=='__main__':main()
