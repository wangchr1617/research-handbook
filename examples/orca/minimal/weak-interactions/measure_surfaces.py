"""测量本例的完整/筛选 IGMH 网格及 mIGM 表面。

python measure_surfaces.py --full-fine WORK/full-020/func2.cub \
  --full-coarse WORK/full-025/func2.cub --screened WORK/grid-020/dg_inter.cub \
  --migm WORK/migm/dg_inter.cub --surface-log WORK/surface-grid/run.log
本例仅处理非周期、正交网格；筛选用 H=1.20、O=1.52 Å 的内置半径。
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from skimage.measure import marching_cubes

from analyze import BOHR_A,cube


def mesh_metrics(field,origin,vectors,level):
    """面积/体积以 Å²/Å³ 返回；体积要求闭合且方向一致的三角网格。"""
    points,faces,_,_=marching_cubes(field,level=level,allow_degenerate=False)
    points=(origin+points@vectors)*BOHR_A
    triangles=points[faces]
    area=float(np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1).sum()/2)
    directed=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    undirected=np.sort(directed,axis=1)
    _,inverse,counts=np.unique(undirected,axis=0,return_inverse=True,return_counts=True)
    edge_balance=np.bincount(inverse,weights=np.where(directed[:,0]<directed[:,1],1,-1))
    closed=bool(np.all(counts==2))
    oriented=bool(np.all(edge_balance==0))
    volume=None
    if closed and oriented:
        shifted=triangles-points.mean(axis=0)
        volume=float(abs(np.einsum('ij,ij->i',shifted[:,0],np.cross(shifted[:,1],shifted[:,2])).sum())/6)
    voxel_volume=float(np.count_nonzero(field>=level)*abs(np.linalg.det(vectors))*BOHR_A**3)
    return dict(level=level,area_A2=area,volume_A3=volume,node_count_volume_A3=voxel_volume,closed=closed,consistently_oriented=oriented,vertices=len(points),triangles=len(faces))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--full-fine',type=Path,required=True)
    ap.add_argument('--full-coarse',type=Path,required=True)
    ap.add_argument('--screened',type=Path,required=True)
    ap.add_argument('--migm',type=Path,required=True)
    ap.add_argument('--surface-log',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,default=Path('.'))
    args=ap.parse_args()
    fine,origin,vectors,atoms=cube(args.full_fine)
    screened,o2,v2,a2=cube(args.screened)
    migm,o3,v3,a3=cube(args.migm)
    for f,o,v,a in [(screened,o2,v2,a2),(migm,o3,v3,a3)]:
        if f.shape!=fine.shape or not np.allclose(o,origin) or not np.allclose(v,vectors) or not np.allclose(a,atoms):
            raise ValueError('细网格比较需要一致的结构、原点和网格')
    if len(atoms)!=6 or set(atoms[:,0])!={1.,8.}:
        raise ValueError('此例的筛选只为给定顺序的六原子 H/O 二聚体定义')
    radii=np.where(atoms[:,0]==1,1.20,1.52)/BOHR_A
    xyz=origin+np.indices(fine.shape).reshape(3,-1).T@vectors
    distance=[np.linalg.norm(xyz[:,None]-atoms[ids,2:],axis=2) for ids in [[0,1,2],[3,4,5]]]
    full_integral=float(fine.sum()*abs(np.linalg.det(vectors)))
    screening=[]
    for scale in [.75,1.,1.25,1.5,2.,2.5]:
        mask=(np.any(distance[0]<scale*radii[:3],axis=1)&np.any(distance[1]<scale*radii[3:],axis=1)).reshape(fine.shape)
        integral=float(fine[mask].sum()*abs(np.linalg.det(vectors)))
        replaced=np.where(mask,fine,0.)
        surface=mesh_metrics(replaced,origin,vectors,.006) if replaced.max()>.006 else None
        screening.append(dict(factor=scale,retained_grid_fraction=float(mask.mean()),integral_e_Bohr=integral,retained_integral_fraction=integral/full_integral,high_grid_points_omitted_at_level_0006=int(np.count_nonzero((fine>=.006)&(~mask))),surface_at_0006=surface))
        if scale==2:
            screen_error=float(np.max(abs(replaced-screened)))
            if screen_error>2e-8:
                raise ValueError('根据几何重建的筛选与程序输出不符')
    coarse,oc,vc,_=cube(args.full_coarse)
    levels=[.003,.006,.012]
    fine_metrics=[mesh_metrics(fine,origin,vectors,x) for x in levels]
    coarse_metrics=[mesh_metrics(coarse,oc,vc,x) for x in levels]
    if any(row['volume_A3'] is None for row in fine_metrics+coarse_metrics):
        raise ValueError('目标表面未闭合或方向不一致，请检查盒子、阈值和网格')
    text=args.surface_log.read_text()
    match_area=re.search(r'Overall surface area:\s*[\d.]+ Bohr\^2\s*\(\s*([\d.]+) Angstrom\^2',text)
    match_volume=re.search(r'Volume:\s*[\d.]+ Bohr\^3\s*\(\s*([\d.]+) Angstrom\^3',text)
    if match_area is None or match_volume is None:
        raise ValueError('Multiwfn 日志缺少面积或体积')
    report=dict(
        model='Fixed planar water dimer; full IGMH field from prior PBE0/def2-SVP density, mIGM from same geometry',
        units=dict(level='e/Bohr^4',area='Angstrom^2',volume='Angstrom^3',integral='e/Bohr'),
        full_fine_integral_e_Bohr=full_integral,
        fine_grid_vectors_Bohr=vectors.tolist(),coarse_grid_vectors_Bohr=vc.tolist(),
        thresholds_fine=fine_metrics,thresholds_coarse=coarse_metrics,
        grid_screening=screening,actual_default_screening_factor=2.,
        reconstructed_mask_max_difference=screen_error,
        mIGM_screened=dict(integral_e_Bohr=float(migm.sum()*abs(np.linalg.det(vectors))),surface_at_0006=mesh_metrics(migm,origin,vectors,.006)),
        Multiwfn_same_Cube_surface=dict(level=.006,algorithm='improved Marching Tetrahedra, existing-grid entry',area_A2=float(match_area[1]),volume_A3=float(match_volume[1])),
        python_surface_algorithm='scikit-image marching_cubes; no mesh smoothing; oriented closed mesh volume; node-count volume separately approximate',
        sha256={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in [('full_fine',args.full_fine),('full_coarse',args.full_coarse),('screened',args.screened),('migm',args.migm)]},
    )
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    (out/'surface-metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    lines=['# grid_Bohr level_e_Bohr4 area_A2 volume_A3 node_count_volume_A3']
    for spacing,rows in [(.20,fine_metrics),(.25,coarse_metrics)]:
        for row in rows:
            lines.append(f"{spacing:.2f} {row['level']:.3f} {row['area_A2']:.9f} {row['volume_A3']:.9f} {row['node_count_volume_A3']:.9f}")
    (out/'surface-metrics.dat').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(full_integral=full_integral,fine=fine_metrics,mIGM=report['mIGM_screened'],mask_error=screen_error),ensure_ascii=False))


if __name__=='__main__':
    main()
