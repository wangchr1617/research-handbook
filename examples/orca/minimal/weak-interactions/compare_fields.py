"""提取同一水二聚体的 RDG/IRI 表面、散点并核对默认筛选。

python compare_fields.py --fields-root WORK --wavefunction orca.molden.input
WORK 包含 rdg、iri、density-gradient、promolecular 四个目录的 func1/func2.cub。
脚本按本例 RDG 密度上限0.05、IRI低密度阈值5e-5及指数1.1核对，均使用原子单位。
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from skimage.measure import marching_cubes

from analyze import BOHR_A, cube


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--fields-root', type=Path, required=True)
    ap.add_argument('--wavefunction', type=Path, required=True)
    ap.add_argument('--output-dir', type=Path, default=Path('.'))
    args = ap.parse_args()
    root = args.fields_root
    loaded = {}
    source_hashes = {}
    reference = None
    for mode in ['rdg','iri','density-gradient','promolecular']:
        for i in [1,2]:
            path = root/mode/f'func{i}.cub'
            values,origin,vectors,atoms = cube(path)
            if reference is None:
                reference = (values.shape,origin,vectors,atoms)
            else:
                shape,o,v,a = reference
                if values.shape!=shape or not np.allclose(origin,o) or not np.allclose(vectors,v) or not np.allclose(atoms,a):
                    raise ValueError('不同函数的原子、原点或网格不一致')
            loaded[mode,i] = values
            source_hashes[f'{mode}/func{i}.cub'] = hashlib.sha256(path.read_bytes()).hexdigest()
    rho,gradient = loaded['density-gradient',1],loaded['density-gradient',2]
    if np.any(rho<=0) or np.any(gradient<=0):
        raise ValueError('本例公式核对需要正密度和非零梯度格点')
    rdg = .161620459673995*gradient/rho**(4/3)
    iri = gradient/rho**1.1
    rdgmask,irimask = rho<.05,rho>5e-5
    rdg_error = float(np.max(abs(loaded['rdg',2][rdgmask]/rdg[rdgmask]-1)))
    iri_error = float(np.max(abs(loaded['iri',2][irimask]/iri[irimask]-1)))
    if rdg_error>2e-5 or iri_error>2e-5:
        raise ValueError('输出与本例公式不符，请核对版本、阈值及指数')
    if not np.all(loaded['rdg',2][~rdgmask]==100) or not np.all(loaded['iri',2][~irimask]==5):
        raise ValueError('默认筛选规则与本例不同，应按实际条件重新核对')
    if not np.array_equal(loaded['rdg',1],loaded['iri',1]):
        raise ValueError('RDG 与 IRI 使用的着色密度不同')
    step = np.diag(vectors)
    colour = loaded['rdg',1]
    interpolate = RegularGridInterpolator(tuple(np.arange(n) for n in colour.shape),colour)
    arrays = {'atoms_A':np.column_stack([atoms[:,0],atoms[:,2:]*BOHR_A])}
    summaries = {}
    for mode,level in [('rdg',.5),('iri',1.)]:
        values = loaded[mode,2]
        vertices,faces,_,_ = marching_cubes(values,level=level,allow_degenerate=False)
        arrays[f'{mode}_vertices_A'] = (origin+vertices*step)*BOHR_A
        arrays[f'{mode}_faces'] = faces
        arrays[f'{mode}_surface_colour'] = interpolate(vertices)
        keep = (values<=2)&(np.abs(colour)<(.05 if mode=='rdg' else .5))
        arrays[f'{mode}_scatter'] = np.column_stack([colour[keep],values[keep]])
        summaries[mode] = dict(isovalue=level,vertices=len(vertices),faces=len(faces),scatter_points=int(keep.sum()))
    promol_s, promol_rdg = loaded['promolecular',1],loaded['promolecular',2]
    if not np.all(promol_rdg[np.abs(promol_s)>=.1]==100):
        raise ValueError('准分子路线的密度上限与本例不同')
    keep = (promol_rdg<=2)&(abs(promol_s)<.1)
    arrays['promolecular_scatter'] = np.column_stack([promol_s[keep],promol_rdg[keep]])
    out = args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'fields-data.npz',**arrays)
    metadata = dict(
        model='Same fixed planar water dimer; PBE0/def2-SVP actual density for RDG/IRI; geometry-only promolecular comparison',
        units=dict(coordinates='Angstrom',colour='e/Bohr^3',RDG='dimensionless',IRI='atomic units with exponent1.1'),
        grid=dict(shape=list(colour.shape),origin_Bohr=origin.tolist(),vectors_Bohr=vectors.tolist()),
        cutoffs=dict(RDG_maxrho=.05,IRI_rhocut=5e-5,IRI_exponent=1.1,RDGprodens_maxrho=.1),
        replaced_grid_points=dict(RDG_high_density=int((~rdgmask).sum()),IRI_low_density=int((~irimask).sum())),
        formula_relative_error=dict(RDG=rdg_error,IRI=iri_error),surfaces=summaries,
        scatter_filter='stored points have descriptor<=2; |sign(lambda2)rho|<0.05 for RDG, <0.5 for IRI; promolecular comparison <0.1',
        colour_range=[-.04,.04],
        original_molden_sha256=hashlib.sha256(args.wavefunction.read_bytes()).hexdigest(),
        electronic_structure_record='interaction-analysis.json',
        source_cube_sha256=source_hashes,
    )
    (out/'fields-analysis.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(replaced=metadata['replaced_grid_points'],error=metadata['formula_relative_error'],surfaces=summaries),ensure_ascii=False))


if __name__=='__main__':
    main()
