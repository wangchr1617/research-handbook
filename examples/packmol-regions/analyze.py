"""检查原子分区与周期最小镜像距离；python analyze.py --work-root WORK --output-dir OUT。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


def xyz(path):
    lines=path.read_text().splitlines();n=int(lines[0]);rows=[line.split() for line in lines[2:]]
    if n<=0 or len(rows)!=n or n%3 or any(len(row)!=4 for row in rows):raise ValueError('要求完整、以O/H/H排列的水分子XYZ')
    labels=[row[0] for row in rows]
    if labels!=['O','H','H']*(n//3):raise ValueError('水分子元素顺序不符')
    coordinates=np.array([[float(v) for v in row[1:]] for row in rows])
    if not np.isfinite(coordinates).all():raise ValueError('坐标含非有限值')
    return coordinates


def minimum_distance(coordinates, box=None):
    displacement=coordinates[:,None,:]-coordinates[None,:,:]
    if box is not None:
        length=np.asarray(box,dtype=float)
        if length.shape!=(3,) or not np.isfinite(length).all() or np.any(length<=0):raise ValueError('仅支持正交正边长盒')
        displacement-=length*np.rint(displacement/length)
    distance=np.linalg.norm(displacement,axis=2)
    different=np.arange(len(coordinates))[:,None]//3!=np.arange(len(coordinates))[None,:]//3
    return float(min(distance[different]))


def analyze(root):
    cfg=json.loads((root/'cases.json').read_text());result={'software':'Packmol 21.2.3','kind':'Geometric initial configurations only; no force field or equilibrium density','cases':{},'source_sha256':{}}
    for name,spec in cfg.items():
        p=root/name;text=(p/'packmol.out').read_text()
        if 'Success!' not in text or not (p/'packed.xyz').exists() or (p/'unused.xyz').exists():raise ValueError('CLI输出覆盖或Packmol终态不符')
        coordinates=xyz(p/'packed.xyz');template=xyz(p/'water.xyz');waters=coordinates.reshape(-1,3,3)
        if len(waters)!=spec['water_count']:raise ValueError('分子数不符')
        target=np.linalg.norm(template[:,None,:]-template[None,:,:],axis=2)
        actual=np.linalg.norm(waters[:,:,None,:]-waters[:,None,:,:],axis=3)
        error=float(np.max(abs(actual-target)))
        direct=minimum_distance(coordinates);periodic=minimum_distance(coordinates,spec['box_Angstrom']) if spec['box_Angstrom'] else None
        if error>3e-6 or (periodic if periodic is not None else direct)<1.998:raise ValueError('分子内部或接触距离不符')
        data={'water_molecules':len(waters),'direct_minimum_Angstrom':direct,'minimum_image_Angstrom':periodic,'rigid_geometry_error_Angstrom':error,'atom_coordinate_min_Angstrom':coordinates.min(axis=0).tolist(),'atom_coordinate_max_Angstrom':coordinates.max(axis=0).tolist()}
        if spec['box_Angstrom']:
            length=np.asarray(spec['box_Angstrom']);delta=coordinates[:,None,:]-coordinates[None,:,:];images=np.rint(delta/length)
            mask=(np.arange(len(coordinates))[:,None]//3!=np.arange(len(coordinates))[None,:]//3)&np.any(images!=0,axis=2)
            data['nonzero_image_atom_pairs_unique']=int(np.sum(mask)//2)
            data['nonzero_image_pair_minimum_Angstrom']=float(min(np.linalg.norm(delta-images*length,axis=2)[mask]))
        if name=='oriented-layer':
            oxygen_z=waters[:,0,2];hydrogen_z=waters[:,1:,2]
            if min(oxygen_z)<1.9999 or max(oxygen_z)>2.2001 or min(hydrogen_z.ravel())<2.4999:raise ValueError('原子区域约束不满足')
            if min(coordinates.ravel())<-.0001 or np.any(coordinates.max(axis=0)>[12.0001,12.0001,4.0001]):raise ValueError('全局区域约束不满足')
            data['oxygen_z_range_Angstrom']=[float(min(oxygen_z)),float(max(oxygen_z))]
            data['hydrogen_z_min_Angstrom']=float(min(hydrogen_z.ravel()))
        result['cases'][name]=data
        for filename in ['packmol.inp','water.xyz','packed.xyz','packmol.out']:
            result['source_sha256'][f'{name}/{filename}']=hashlib.sha256((p/filename).read_bytes()).hexdigest()
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work-root',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    result=analyze(args.work_root);args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for name in result['cases']:shutil.copy2(args.work_root/name/'packed.xyz',args.output_dir/f'{name}.xyz')
