"""从moments-nocv.npz重绘Zn投影质心和水二聚体变形密度实际网格层。

python plot.py --data moments-nocv.npz --moments-output moments.png --nocv-output nocv.png
依赖numpy/matplotlib。坐标Å、密度e/Bohr^3；本征值与模型能量使用不同轴。
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--moments-output',type=Path,required=True);p.add_argument('--nocv-output',type=Path,required=True)
    args=p.parse_args();a=np.load(args.data);ev=27.2113838
    fig,axes=plt.subplots(1,2,figsize=(11,4.6),constrained_layout=True)
    for ax,names,title in [(axes[0],['zn_dos_narrow','zn_dos_wide'],'Integral window -1.0 to 0.8 Ha (zoom)' ),(axes[1],['zn_dos_short_narrow','zn_dos_short'],'Window -0.4 to -0.3 Ha')]:
        for name,label,color in zip(names,['FWHM 0.02 Ha','FWHM 0.10 Ha'],['tab:blue','tab:orange']):
            table=a[name];x,y=table[:,0],table[:,2]
            # 图中横轴为原子单位，纵轴保持相应每Ha的投影态数。
            centre=np.sum(x*y)/np.sum(y)
            ax.plot(x,y,label=label,color=color)
            ax.axvline(centre,color=color,ls=':',lw=1)
        ax.set(xlabel='Orbital energy (Ha)',ylabel='D-projected states / Ha',title=title)
        ax.legend(fontsize=8)
    axes[0].set_xlim(-.55,-.15)
    fig.suptitle('Isolated Zn, PBE / def2-SVP; D-subspace moment check\nWindow truncation and broadening can change the centroid')
    args.moments_output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.moments_output,dpi=180);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(10,8),constrained_layout=True)
    origin,v=a['origin_Bohr'],a['vectors_Bohr'];bohr=.529177210903
    x=(origin[0]+np.arange(a['pair1'].shape[0])*v[0,0])*bohr
    y=(origin[1]+np.arange(a['pair1'].shape[1])*v[1,1])*bohr
    keys=['pair1','pauli','orbital','total'];titles=['NOCV pair 1','Pauli: frozen - fragment sum','Orbital: actual - frozen','Total: actual - fragment sum']
    maximum=max(np.max(abs(a[k])) for k in keys)
    norm=SymLogNorm(linthresh=1e-4,vmin=-maximum,vmax=maximum,base=10)
    for ax,key,title in zip(axes.flat,keys,titles):
        artist=ax.pcolormesh(x,y,a[key].T,shading='nearest',cmap='RdBu_r',norm=norm)
        ax.set(title=title,xlabel='x (Å)',ylabel='y (Å)',aspect='equal')
    fig.colorbar(artist,ax=axes,label='Density change (e / Bohr³), symmetric log scale',shrink=.85)
    z=(origin[2]+int(a['z_index'])*v[2,2])*bohr
    fig.suptitle(f'Fixed water dimer, PBE0 / def2-SVP; slice z = {z:.3f} Å\nBlue: density decrease; red: increase; same color scale')
    args.nocv_output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.nocv_output,dpi=180);plt.close(fig)


if __name__=='__main__':main()
