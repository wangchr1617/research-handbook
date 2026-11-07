"""重绘实际 RDG/IRI 等值面和散点：python plot_fields.py --data-dir . --output fields.png。"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap,Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-dir',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--output',type=Path,default=Path('fields.png'))
    args=ap.parse_args()
    d=np.load(args.data_dir/'fields-data.npz')
    m=json.loads((args.data_dir/'fields-analysis.json').read_text())
    cmap=LinearSegmentedColormap.from_list('blue_green_red',['#2451b3','#37b778','#d93b38'])
    norm=Normalize(*m['colour_range'])
    fig=plt.figure(figsize=(11,8),layout='constrained')
    fig.get_layout_engine().set(wspace=.12,hspace=.06)
    atoms=d['atoms_A']
    axes=[]
    for index,mode in enumerate(['rdg','iri']):
        ax=fig.add_subplot(2,2,index+1,projection='3d')
        axes.append(ax)
        faces=d[f'{mode}_faces'];triangles=d[f'{mode}_vertices_A'][faces]
        colours=d[f'{mode}_surface_colour'][faces].mean(axis=1)
        ax.add_collection3d(Poly3DCollection(triangles,facecolors=cmap(norm(colours)),linewidths=0,alpha=.93))
        for i,j in [(0,1),(0,2),(3,4),(3,5)]:ax.plot(*atoms[[i,j],1:].T,color='.5',lw=1.8)
        for i,a in enumerate(atoms):
            ax.scatter(*a[1:],s=70 if a[0]==8 else 30,color='#cf3c35' if a[0]==8 else '#eeeeee',edgecolors='.35',depthshade=False)
            ax.text(*a[1:],str(i+1),fontsize=7)
        ax.set(xlim=(-.7,4.),ylim=(-1.5,1.5),zlim=(-1.5,1.5),xlabel='x (Angstrom)',ylabel='y (Angstrom)',zlabel='z (Angstrom)')
        ax.set_box_aspect((4.7,3,3));ax.view_init(elev=22,azim=-64)
        ax.zaxis.label.set_fontsize(8);ax.zaxis.labelpad=0
        level=m['surfaces'][mode]['isovalue']
        condition='rho < 0.05 a.u.' if mode=='rdg' else 'a = 1.1; rho > 5e-5 a.u.'
        ax.set_title(f'{mode.upper()} = {level:g} | {condition}',fontsize=10)
        scatter=fig.add_subplot(2,2,index+3)
        axes.append(scatter)
        points=d[f'{mode}_scatter']
        scatter.scatter(points[:,0],points[:,1],c=points[:,0],cmap=cmap,norm=norm,s=2,alpha=.5,rasterized=True)
        if mode=='rdg':
            pro=d['promolecular_scatter']
            scatter.scatter(pro[:,0],pro[:,1],color='.55',s=1,alpha=.18,label='promolecular; different cutoff')
            scatter.legend(fontsize=7,loc='upper right')
        scatter.axhline(level,color='.35',lw=.8,ls='--')
        scatter.set(xlim=(-.05,.05) if mode=='rdg' else (-.5,.05),ylim=(0,2),xlabel=r'$\mathrm{sign}(\lambda_2)\rho$ ($e/a_0^3$)',ylabel='RDG' if mode=='rdg' else 'IRI (a.u.)')
        scatter.set_title('Every stored grid point; no fitted curve',fontsize=9)
    sm=matplotlib.cm.ScalarMappable(norm=norm,cmap=cmap)
    fig.colorbar(sm,ax=axes,shrink=.55,pad=.03,label=r'$\mathrm{sign}(\lambda_2)\rho$ ($e/a_0^3$)')
    fig.suptitle('Water dimer | RDG/IRI from PBE0/def2-SVP | fixed teaching geometry',fontsize=12)
    fig.savefig(args.output,dpi=180)
    plt.close(fig)


if __name__=='__main__':
    main()
