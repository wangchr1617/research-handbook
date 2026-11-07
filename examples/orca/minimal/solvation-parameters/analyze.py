"""核对溶剂参数、能量与 CM5，绘制独立 Born 球模型；python analyze.py --work-root WORK --output-dir OUT。"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
HARTREE_KJ = 4.3597447222071e-18*6.02214076e23/1000
BOHR_ANGSTROM = .529177210903
R = 8.31446261815324


def native(folder):
    text = (folder/'calc.out').read_text()
    if 'ORCA TERMINATED NORMALLY' not in text or 'error termination' in text.lower():
        raise ValueError(f'原生任务未正常结束：{folder}')
    values = re.findall(r'FINAL SINGLE POINT ENERGY\s+([-\d.]+)', text)
    if not values:
        raise ValueError('未找到最终单点能')
    energy = float(values[-1])
    result = {'final_energy_Hartree': energy}
    for label, pattern in [('CPCM_dielectric_Hartree', r'CPCM Dielectric\s+:\s+([-\d.]+)'),
                           ('SMD_CDS_Hartree', r'SMD CDS \(Gcds\)\s+:\s+([-\d.]+)')]:
        terms = re.findall(pattern, text)
        result[label] = float(terms[-1]) if terms else 0.
        if folder.name in ['br-smd', 'br-smd18', 'water-smd', 'water-gil'] and not terms:
            raise ValueError('溶剂任务缺少显式能量分量')
    radius = re.findall(r'Radius for Br used is\s+([\d.]+) Bohr \(=\s+([\d.]+) Ang.', text)
    if radius:
        result['Br_radius_Angstrom'] = float(radius[-1][1])
    descriptors = {}
    for name in ['Epsilon', 'Refrac', 'Soln', 'Soln25', 'Sola', 'Solb', 'Solg', 'Solc', 'Solh']:
        match = re.findall(r'(?m)^\s*'+name+r'\s+\.\.\.\s+([-\d.]+)', text)
        if match:
            descriptors[name] = float(match[-1])
    result['printed_solvent_descriptors'] = descriptors
    if not np.isfinite([energy, result['CPCM_dielectric_Hartree'], result['SMD_CDS_Hartree']]).all():
        raise ValueError('能量含非有限值')
    return result, text


def born(radius_angstrom, epsilon, charge=1.):
    """中心点电荷、球形空腔；返回理想 Born 极化自由能 kJ/mol。"""
    radius = np.asarray(radius_angstrom, dtype=float)
    eps = np.asarray(epsilon, dtype=float)
    if not np.isfinite(radius).all() or not np.isfinite(eps).all() or not np.isfinite(charge) or np.any(radius <= 0) or np.any(eps < 1):
        raise ValueError('Born 半径须正，介电常数须至少为 1，参数须有限')
    # In atomic units: -q²/(2a) * (1-1/epsilon), radius a in Bohr.
    return -.5*charge**2/(radius/BOHR_ANGSTROM)*(1-1/eps)*HARTREE_KJ


def count_descriptors(composition, aromatic_carbons):
    heavy = sum(n for element, n in composition.items() if element != 'H')
    if heavy <= 0 or aromatic_carbons < 0 or aromatic_carbons > composition.get('C', 0) or any(not isinstance(n, int) or n < 0 for n in composition.values()):
        raise ValueError('组成或芳香碳计数不符')
    return {'heavy_atoms': heavy, 'aromaticity': aromatic_carbons/heavy,
            'electronegative_halogenicity': sum(composition.get(x, 0) for x in ['F', 'Cl', 'Br'])/heavy}


def analyze(root):
    result = {'software': 'ORCA 6.1.1; Multiwfn 2026.7.15', 'source_sha256': {}, 'stationary_points': {},
              'models': {}, 'definition': 'Fixed-geometry total SMD energy minus matching gas energy; equal-concentration solvation model convention, no extra thermal/standard-state term included'}
    for name in ['br-gas', 'br-smd', 'br-smd18', 'water-opt', 'water-smd', 'water-gil']:
        folder = root/name
        if (folder/'calc.inp').read_bytes() != (HERE/f'{name}.inp').read_bytes():
            raise ValueError('原生输入与公开模板不一致')
        values, text = native(folder)
        if name == 'water-opt':
            if 'THE OPTIMIZATION HAS CONVERGED' not in text:
                raise ValueError('水结构优化未收敛')
            hess = (folder/'calc.hess').read_text().splitlines()
            i = hess.index('$vibrational_frequencies')+1
            freq = [float(hess[i+1+j].split()[1]) for j in range(int(hess[i]))]
            if len(freq) != 9 or min(freq[6:]) <= 0:
                raise ValueError('水的内部模式不全为正')
            values['internal_frequencies_cm-1'] = freq[6:]
        result['models'][name] = values
        for filename in ['calc.inp', 'structure.xyz', 'calc.out']:
            path = folder/filename; result['source_sha256'][f'{name}/{filename}'] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name, gas in [('br-smd', 'br-gas'), ('br-smd18', 'br-gas'), ('water-smd', 'water-opt'), ('water-gil', 'water-opt')]:
        record = result['models'][name]
        delta = record['final_energy_Hartree']-result['models'][gas]['final_energy_Hartree']
        record['solvation_model_difference_kJ_mol'] = delta*HARTREE_KJ
        # Final SMD energy already includes CDS; dielectric term alone omits
        # solute electronic reorganization under the self-consistent reaction field.
        record['solute_reorganization_kJ_mol'] = (delta-record['SMD_CDS_Hartree']-record['CPCM_dielectric_Hartree'])*HARTREE_KJ
    source = root/'water-opt/calc.xyz'
    for name in ['water-smd', 'water-gil']:
        if (root/name/'structure.xyz').read_bytes() != source.read_bytes():
            raise ValueError('溶剂比较没有使用相同最终几何')
    coordinate_rows = [row.split() for row in source.read_text().splitlines()[2:5]]
    charge_path = root/'water-opt/calc.chg'
    charge_rows = [row.split() for row in charge_path.read_text().splitlines() if row.strip()]
    if [row[0] for row in charge_rows] != ['O', 'H', 'H'] or [row[0] for row in coordinate_rows] != ['O', 'H', 'H']:
        raise ValueError('元素顺序不符')
    xyz = np.array([[float(v) for v in row[1:4]] for row in coordinate_rows])
    charge_xyz = np.array([[float(v) for v in row[1:4]] for row in charge_rows])
    charges = np.array([float(row[4]) for row in charge_rows])
    if not np.isfinite(charges).all() or max(abs(charges.sum()), np.max(abs(xyz-charge_xyz))) > 1e-5:
        raise ValueError('电荷和或电荷表几何异常')
    result['CM5'] = {'level': 'ORCA B3LYP/G (VWN3) / def2-TZVP, gas-phase optimized H2O',
                     'source': 'Multiwfn CM5, spherical free-atom densities, native electron-population normalization, not 1.2*CM5',
                     'elements': ['O', 'H', 'H'], 'atomic_numbers': [8, 1, 1], 'coordinates_Angstrom': xyz.tolist(),
                     'charges_e': charges.tolist(), 'charge_sum_e': float(charges.sum()),
                     'scope': 'Prepared charge/geometry data; external uESE executable is not invoked by this script'}
    for filename in ['calc.gbw', 'calc.hess', 'calc.xyz', 'calc.molden.input', 'conversion.out', 'cm5.menu', 'cm5.out', 'calc.chg']:
        path = root/'water-opt'/filename; result['source_sha256'][f'water-opt/{filename}'] = hashlib.sha256(path.read_bytes()).hexdigest()
    composition = {'C': 6, 'H': 11, 'N': 2, 'B': 1, 'F': 4}
    result['ionic_liquid_composition'] = {'formula_unit': '[EMIM][BF4]', 'composition': composition, **count_descriptors(composition, 3),
                                         'scope': 'GIL average parameters plus formula-unit fractions, not measured pure-solvent descriptors'}
    radii = np.linspace(2., 3.5, 151)
    result['Born_model'] = {'kind': 'Independent central point-charge sphere; not the molecular SMD solver',
                            'radius_Angstrom': radii.tolist(), 'epsilon': 11.5,
                            'polarization_kJ_mol': born(radii, 11.5).tolist()}
    result['standard_state'] = {'T_K': 298.15, 'p_Pa': 101325., 'c_mol_m3': 1000.,
                                'single_species_p_to_c_correction_kJ_mol': R*298.15*np.log(1000*R*298.15/101325)/1000,
                                'surface_tension_mN_m_to_cal_mol_Angstrom2': .001*6.02214076e23*1e-20/4.184}
    return result


def write_outputs(result, output):
    output.mkdir(parents=True, exist_ok=True)
    (output/'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    charge = result['CM5']
    lines = ['H2O gas B3LYP/G-def2-TZVP CM5; coordinates in angstrom', ' Atomic coordinates']
    for z, xyz in zip(charge['atomic_numbers'], charge['coordinates_Angstrom']):
        lines.append(f'{z:3d} '+' '.join(f'{v:.10f}' for v in xyz))
    lines += ['', ' Ground state charges', ' '.join(f'{v:.10f}' for v in charge['charges_e']), '']
    (output/'water.cm5-input').write_text('\n'.join(lines)+'\n')
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), constrained_layout=True)
    names = ['br-smd', 'br-smd18']; values = [result['models'][name]['solvation_model_difference_kJ_mol'] for name in names]
    axes[0].bar(['SMD: Br radius 3.06 Å', 'SMD18: Br radius 2.60 Å'], values, color=['tab:blue', 'tab:orange'])
    axes[0].set(ylabel='E(solvent) - E(gas) / kJ mol$^{-1}$', title='Br$^-$: M06-2X / def2-TZVPD, acetonitrile')
    axes[0].tick_params(axis='x', labelsize=8)
    r = np.array(result['Born_model']['radius_Angstrom'])
    for eps in [2., 11.5, 80.]:
        axes[1].plot(r, born(r, eps), label=f'$\\epsilon_r$ = {eps:g}')
    axes[1].set(xlabel='Sphere radius / Å', ylabel='Born polarization / kJ mol$^{-1}$', title='Independent point-charge model, |q| = e')
    axes[1].legend(fontsize=8); axes[1].grid(alpha=.2)
    fig.savefig(output/'solvation-parameters.png', dpi=180); plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    write_outputs(analyze(args.work_root), args.output_dir)
