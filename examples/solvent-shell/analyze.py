"""核对 Packmol 分子清单并整分子提取壳层，另计算固定 Born 半径模型。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from prepare import xyz_text

HERE = Path(__file__).resolve().parent
COULOMB = 6.02214076e23*1.602176634e-19**2/(4*np.pi*8.8541878128e-12)*1e10/1000


def read_xyz(path):
    lines = path.read_text().splitlines()
    count = int(lines[0])
    if count <= 0 or len(lines) < count+2 or any(line.strip() for line in lines[count+2:]):
        raise ValueError('仅接受完整单帧 XYZ')
    rows = [line.split() for line in lines[2:count+2]]
    if any(len(row) != 4 for row in rows):
        raise ValueError('XYZ 列数不符')
    labels = [row[0] for row in rows]
    coordinates = np.array([[float(v) for v in row[1:]] for row in rows])
    if not np.isfinite(coordinates).all():
        raise ValueError('坐标含非有限值')
    return labels, coordinates


def groups(manifest, labels):
    indices = [i for molecule in manifest for i in molecule['atom_indices_0based']]
    if sorted(indices) != list(range(len(labels))) or len({m['molecule_id'] for m in manifest}) != len(manifest):
        raise ValueError('分子清单未构成原子集合的唯一分区')
    if len([m for m in manifest if m['kind'] == 'solute']) != 1:
        raise ValueError('此例要求一个明确的溶质分子')
    for molecule in manifest:
        if [labels[i] for i in molecule['atom_indices_0based']] != molecule['elements']:
            raise ValueError('元素顺序与分子清单不符')
    return manifest


def shell(coordinates, manifest, cutoff):
    """非周期单帧 Å 坐标；任一溶剂原子进入阈值即保留整个分子。"""
    if not np.isfinite(cutoff) or cutoff <= 0:
        raise ValueError('壳层阈值须为有限正数')
    solute = next(m for m in manifest if m['kind'] == 'solute')
    solute_xyz = coordinates[solute['atom_indices_0based']]
    selected = [solute]; atom_only = len(solute_xyz); distances = []
    for molecule in manifest:
        if molecule['kind'] == 'solute':
            continue
        xyz = coordinates[molecule['atom_indices_0based']]
        nearest = np.min(np.linalg.norm(xyz[:, None, :]-solute_xyz[None, :, :], axis=2), axis=1)
        distances.append({'molecule_id': molecule['molecule_id'], 'nearest_atom_distance_Angstrom': float(min(nearest))})
        atom_only += int(np.sum(nearest <= cutoff))
        if min(nearest) <= cutoff:
            selected.append(molecule)
    indices = [i for molecule in selected for i in molecule['atom_indices_0based']]
    return {'cutoff_Angstrom': cutoff, 'water_count': len(selected)-1,
            'whole_molecule_atom_count': len(indices), 'atom_only_atom_count': atom_only,
            'selected_molecule_ids': [m['molecule_id'] for m in selected],
            'selected_atom_indices_0based': indices, 'water_nearest_distances': distances}


def gb_polar(coordinates, charges, born_radii, eps_in=1., eps_out=78.5):
    """固定有效 Born 半径的 Still 核；不是 OBC/HCT 半径算法或完整力场。"""
    xyz = np.asarray(coordinates, dtype=float); q = np.asarray(charges, dtype=float); radii = np.asarray(born_radii, dtype=float)
    if xyz.shape != (len(q), 3) or radii.shape != q.shape or not np.isfinite(xyz).all() or not np.isfinite(q).all() or not np.isfinite(radii).all() or not np.isfinite([eps_in, eps_out]).all() or min(eps_in, eps_out) <= 0 or np.any(radii <= 0):
        raise ValueError('坐标、电荷、Born 半径或介电常数无效')
    r2 = np.sum((xyz[:, None, :]-xyz[None, :, :])**2, axis=2)
    products = radii[:, None]*radii[None, :]
    f = np.sqrt(r2+products*np.exp(-r2/(4*products)))
    return float(-.5*COULOMB*(1/eps_in-1/eps_out)*np.sum(q[:, None]*q[None, :]/f))


def analyze(root):
    cfg = json.loads((HERE/'protocol.json').read_text())
    result = {'software': 'Packmol 21.2.3', 'definition': 'Packing geometry, not energy minimization or equilibrium sampling; nonperiodic complete-molecule selection by any-atom distance',
              'protocol': cfg, 'source_sha256': {}, 'packings': []}
    for seed in cfg['seeds']:
        folder = root/f'seed-{seed}'
        if 'Success!' not in (folder/'packmol.out').read_text():
            raise ValueError('Packmol 未报告成功')
        labels, xyz = read_xyz(folder/'packed.xyz')
        manifest = groups(json.loads((folder/'molecules.json').read_text()), labels)
        if len(manifest) != cfg['water_molecules']+1 or len(labels) != 5+3*cfg['water_molecules']:
            raise ValueError('分子或原子数不符')
        source_labels, solute_xyz = read_xyz(folder/'solute.xyz')
        if labels[:5] != source_labels or np.max(abs(xyz[:5]-solute_xyz)) > 2e-6:
            raise ValueError('固定溶质发生移动')
        atom_molecules = np.empty(len(labels), dtype=int)
        template_labels, template_water = read_xyz(folder/'water.xyz')
        template_distances = np.linalg.norm(template_water[:, None, :]-template_water[None, :, :], axis=2)
        rigid_error = 0.
        for molecule in manifest:
            idx = molecule['atom_indices_0based']; atom_molecules[idx] = molecule['molecule_id']
            if molecule['kind'] == 'water':
                w = xyz[idx]
                rigid_error = max(rigid_error, float(np.max(abs(np.linalg.norm(w[:, None, :]-w[None, :, :], axis=2)-template_distances))))
        pair = np.linalg.norm(xyz[:, None, :]-xyz[None, :, :], axis=2)
        minimum = float(np.min(pair[atom_molecules[:, None] != atom_molecules[None, :]]))
        if minimum < cfg['intermolecular_tolerance_angstrom']-.002 or rigid_error > 3e-6:
            raise ValueError('分子间接触或水分子刚体几何不符')
        max_radius = float(np.max(np.linalg.norm(xyz[5:], axis=1)))
        if max_radius > cfg['sphere_radius_angstrom']+.002:
            raise ValueError('水分子原子超出装填球约束')
        selections = [shell(xyz, manifest, cutoff) for cutoff in cfg['shell_cutoffs_angstrom']]
        result['packings'].append({'seed': seed, 'atoms': len(labels), 'minimum_intermolecular_distance_Angstrom': minimum,
                                    'maximum_solvent_atom_radius_Angstrom': max_radius, 'water_rigid_distance_max_error_Angstrom': rigid_error,
                                    'selections': selections})
        for name in ['packmol.inp', 'solute.xyz', 'water.xyz', 'molecules.json', 'packmol.out', 'packed.xyz']:
            result['source_sha256'][f'seed-{seed}/{name}'] = hashlib.sha256((folder/name).read_bytes()).hexdigest()
    distances = np.linspace(2., 20., 181); alpha = 1.5
    self_energy = gb_polar([[0, 0, 0]], [1], [alpha])+gb_polar([[0, 0, 0]], [-1], [alpha])
    rows = []
    for distance in distances:
        polar = gb_polar([[0, 0, 0], [distance, 0, 0]], [1, -1], [alpha, alpha])
        vacuum = -COULOMB/distance
        rows.append({'distance_Angstrom': float(distance), 'polar_kJ_mol': polar,
                     'vacuum_Coulomb_kJ_mol': vacuum, 'GB_interaction_relative_to_fixed_isolated_self_kJ_mol': vacuum+polar-self_energy,
                     'uniform_dielectric_Coulomb_kJ_mol': vacuum/78.5})
    result['GB_model'] = {'kind': 'Independent opposite-charge pair with externally fixed Born radii; no ionic-strength term, no nonpolar term or MD dynamics',
                          'charges_e': [1, -1], 'Born_radii_Angstrom': [alpha, alpha], 'eps_in': 1., 'eps_out': 78.5,
                          'isolated_self_sum_kJ_mol': self_energy, 'rows': rows}
    return result


def write_outputs(result, root, output):
    output.mkdir(parents=True, exist_ok=True)
    (output/'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    for packing in result['packings']:
        seed = packing['seed']; source = root/f'seed-{seed}'
        shutil.copy2(source/'packed.xyz', output/f'packed-{seed}.xyz')
        labels, xyz = read_xyz(source/'packed.xyz')
        selection = next(s for s in packing['selections'] if s['cutoff_Angstrom'] == 4.)
        indices = selection['selected_atom_indices_0based']
        (output/f'shell-{seed}-4A.xyz').write_text(xyz_text([labels[i] for i in indices], xyz[indices], f'Complete-molecule shell; seed={seed}; any-atom cutoff=4 angstrom; packing geometry'))
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), constrained_layout=True)
    for packing in result['packings']:
        selections = packing['selections']
        axes[0].plot([s['cutoff_Angstrom'] for s in selections], [s['water_count'] for s in selections], 'o-', label=f"Packing seed {packing['seed']}")
    axes[0].set(xlabel='Any-atom distance from solute / Å', ylabel='Selected whole water molecules', title='CH$_4$ + 64 waters: initial packings')
    axes[0].legend(fontsize=8)
    rows = result['GB_model']['rows']; x = [r['distance_Angstrom'] for r in rows]
    axes[1].plot(x, [r['GB_interaction_relative_to_fixed_isolated_self_kJ_mol'] for r in rows], label='Fixed-radius GB + vacuum, minus self terms')
    axes[1].plot(x, [r['uniform_dielectric_Coulomb_kJ_mol'] for r in rows], '--', label='Uniform dielectric Coulomb')
    axes[1].set(xlabel='Opposite-charge separation / Å', ylabel='Pair interaction / kJ mol$^{-1}$', title='Independent two-charge model')
    axes[1].legend(fontsize=7)
    for ax in axes: ax.grid(alpha=.2)
    fig.savefig(output/'shell-and-gb.png', dpi=180); plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    write_outputs(analyze(args.work_root), args.work_root, args.output_dir)
