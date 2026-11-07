"""从orbital-data.npz重绘DOS与片段轨道图。

python plot.py --data orbital-data.npz --output dos.png --cda-output cda.png
DOS空间轨道计数一次；横轴eV，纵轴按Ha→eV的Jacobian转换。
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cda-output',type=Path,required=True)
    args=p.parse_args();a=np.load(args.data);ev=27.2113838
    narrow=a['dos_002'];wide=a['dos_005'];hir=a['dos_hirshfeld']
    x=narrow[:,0]*ev;homo=a['energy_Ha'][9]*ev;lumo=a['energy_Ha'][10]*ev
    fig,axes=plt.subplots(3,1,figsize=(10,9),sharex=True,constrained_layout=True)
    axes[0].plot(x,narrow[:,1]/ev,label='FWHM 0.544 eV')
    axes[0].plot(wide[:,0]*ev,wide[:,1]/ev,label='FWHM 1.361 eV',ls='--')
    axes[0].set(ylabel='States / eV',title='Same discrete levels; different Gaussian widths')
    axes[1].plot(x,narrow[:,1]/ev,color='black',lw=1,label='Total')
    axes[1].plot(x,hir[:,2]/ev,label='Water A (Hirshfeld)')
    axes[1].plot(x,hir[:,3]/ev,label='Water B (Hirshfeld)')
    axes[1].set(ylabel='States / eV',title='Two disjoint atomic fragments cover the whole dimer')
    axes[2].plot(x,narrow[:,2]/ev,color='purple',label='OPDOS A-B (Mulliken)')
    axes[2].axhline(0,color='.5',lw=.7)
    axes[2].set(xlabel='Orbital energy (eV)',ylabel='Overlap weight / eV',title='Signed overlap weights; occupations applied separately')
    for ax in axes:
        ax.axvline(homo,color='black',ls=':',lw=.8,label='HOMO' if ax is axes[0] else None)
        ax.axvline(lumo,color='.5',ls=':',lw=.8,label='LUMO' if ax is axes[0] else None)
        ax.set_xlim(-30,30);ax.legend(fontsize=9,loc='upper right')
    fig.suptitle('Fixed water dimer, PBE0 / def2-SVP; one count per spatial orbital')
    args.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.output,dpi=180);plt.close(fig)
    fig,(left,right)=plt.subplots(1,2,figsize=(12,7),constrained_layout=True,gridspec_kw={'width_ratios':[1.4,1]})
    energies=[a['FO_energies_Ha'][:24]*ev,a['energy_Ha']*ev,a['FO_energies_Ha'][24:]*ev]
    for position,levels in enumerate(energies):
        for i,value in enumerate(levels):
            if -16 <= value <= 8:
                left.hlines(value,position-.1,position+.1,color=['tab:blue','black','tab:orange'][position],ls='-' if i<(10 if position==1 else 5) else '--')
                dy=0
                if i>0 and abs(value-levels[i-1])<.35: dy=6
                elif i+1<len(levels) and abs(value-levels[i+1])<.35: dy=-6
                left.annotate(str(i+1),(position+.1,value),xytext=(4,dy),textcoords='offset points',fontsize=7,va='center')
    comp=a['FO_compositions']
    for i,ce in enumerate(energies[1]):
        if not -16<=ce<=8:continue
        for j,fe in enumerate(a['FO_energies_Ha']*ev):
            if not -16<=fe<=8 or comp[j,i]<.2:continue
            left.plot([0 if j<24 else 2,1],[fe,ce],color='tab:blue' if j<24 else 'tab:orange',alpha=.35,lw=.8,zorder=0)
    left.set(xticks=[0,1,2],xticklabels=['Water A','Complex','Water B'],ylabel='Orbital energy (eV)',ylim=(-16.5,8.5),xlim=(-.25,2.4),title='FO contributions >=20%; window -16 to 8 eV')
    idx=np.arange(3,11);b=.24
    for offset,key,label in [(-b,'cda_d','d: A to B'),(0,'cda_b','b: B to A'),(b,'cda_r','r: occupied mixing')]:
        right.barh(idx+offset,a[key][2:10],height=b,label=label)
    right.axvline(0,color='.4',lw=.7);right.invert_yaxis()
    right.set(xlabel='Signed GCDA contribution (electrons)',ylabel='Complex orbital index',yticks=idx,title='Valence occupied orbitals; refocc = 2')
    right.legend(fontsize=8,loc='lower right')
    fig.suptitle('Fixed geometry; neutral singlet fragments; no ghost centres\nFO links are composition weights, not interaction energies')
    args.cda_output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.cda_output,dpi=180);plt.close(fig)


if __name__=='__main__':main()
