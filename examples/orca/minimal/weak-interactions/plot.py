"""重绘本例真实 IGMH 数据：python plot.py [--data-dir .] [--output figure.png]。"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--output', type=Path, default=Path('interaction.png'))
    args = ap.parse_args()
    d = np.load(args.data_dir/'interaction-data.npz')
    m = json.loads((args.data_dir/'interaction-analysis.json').read_text())
    level = m['surface']['isovalue_e_Bohr4']
    cmap = LinearSegmentedColormap.from_list('blue_green_red',['#2451b3','#37b778','#d93b38'])
    norm = Normalize(*m['surface']['colour_range'])
    fig = plt.figure(figsize=(11,4.6),layout='constrained')
    fig.get_layout_engine().set(wspace=.16)
    ax = fig.add_subplot(121, projection='3d')
    triangles = d['vertices_A'][d['faces']]
    facecolour = d['surface_colour'][d['faces']].mean(axis=1)
    ax.add_collection3d(Poly3DCollection(triangles,facecolors=cmap(norm(facecolour)),linewidths=0,alpha=.93))
    atoms = d['atoms_A']
    # 连线只标明输入几何中的分子内部连接，不代表 QTAIM 键径。
    bonds = [(0,1),(0,2),(3,4),(3,5)]
    for i,j in bonds:
        ax.plot(*atoms[[i,j],1:].T,color='.45',lw=2)
    for i,a in enumerate(atoms):
        ax.scatter(*a[1:],s=95 if a[0]==8 else 38,color='#cf3c35' if a[0]==8 else '#eeeeee',edgecolors='.35',depthshade=False)
        ax.text(*a[1:],str(i+1),fontsize=8)
    ax.set(xlim=(-.7,4.0),ylim=(-1.5,1.5),zlim=(-1.5,1.5),xlabel='x (Angstrom)',ylabel='y (Angstrom)',zlabel='z (Angstrom)')
    ax.set_box_aspect((4.7,3,3)); ax.view_init(elev=22,azim=-64)
    ax.zaxis.label.set_fontsize(9)
    ax.zaxis.labelpad=0
    ax.set_title(r'$\delta g_{inter}=' + f'{level:g}' + r'$ a.u. surface',fontsize=11)
    plane = fig.add_subplot(122)
    x,y = d['x_A'],d['y_A']
    dg,colour = d['delta_g_plane'],d['colour_plane']
    mask = np.ma.masked_where(dg.T < level,colour.T)
    plane.pcolormesh(x,y,mask,cmap=cmap,norm=norm,shading='nearest',rasterized=True)
    plane.contour(x,y,dg.T,levels=[level,2*level,4*level],colors='.35',linewidths=.65)
    for i,j in bonds:plane.plot(atoms[[i,j],1],atoms[[i,j],2],color='.45',lw=1.5)
    for i,a in enumerate(atoms):
        plane.scatter(a[1],a[2],s=80 if a[0]==8 else 30,color='#cf3c35' if a[0]==8 else '#eeeeee',edgecolors='.35',zorder=4)
        plane.annotate(str(i+1),(a[1],a[2]),xytext=(4,5),textcoords='offset points',fontsize=8)
    plane.set(xlim=(-.7,4.),ylim=(-1.6,1.6),xlabel='x (Angstrom)',ylabel='y (Angstrom)',title=f'Actual slice: z = {m["slice"]["z_A"]:.4f} Angstrom')
    plane.set_aspect('equal')
    sm = matplotlib.cm.ScalarMappable(norm=norm,cmap=cmap)
    fig.colorbar(sm,ax=[ax,plane],shrink=.65,pad=.04,label=r'$\mathrm{sign}(\lambda_2)\rho$ ($e/a_0^3$)')
    fig.suptitle('Water dimer | PBE0/def2-SVP | fixed teaching geometry',fontsize=12)
    fig.savefig(args.output,dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
