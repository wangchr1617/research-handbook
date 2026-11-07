#!/usr/bin/env python3
"""生成结构格式往返与同位素转动常数示例。

用法：python3 analyze.py --output-dir /tmp/structure-formats-new
依赖 ASE、NumPy、SciPy；仅后处理，坐标 Å，CM5 电荷 e。
"""
import argparse
import hashlib
import json
from pathlib import Path

import ase
from ase import Atoms
from ase.cell import Cell
from ase.data import atomic_numbers
from ase.io import read, write
from ase.calculators.singlepoint import SinglePointCalculator
import numpy as np
from scipy.constants import h, atomic_mass, c

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'examples/orca/minimal/solvation-parameters/analysis.json'


def rotational_constants(positions, masses):
    """返回三个主惯量和刚性转子常数；质量 u，坐标 Å。"""
    x, m = np.asarray(positions, dtype=float), np.asarray(masses, dtype=float)
    if x.ndim != 2 or x.shape[1] != 3 or m.shape != (len(x),) or len(x) < 2:
        raise ValueError('需要 N×3 坐标及 N 个质量')
    if not np.isfinite(x).all() or not np.isfinite(m).all() or np.any(m <= 0):
        raise ValueError('坐标有限、质量有限且为正')
    centered = x-np.sum(x*m[:, None], axis=0)/m.sum()
    inertia = sum(mi*(np.dot(r, r)*np.eye(3)-np.outer(r, r)) for mi, r in zip(m, centered))
    moments = np.linalg.eigvalsh(inertia)
    if moments[0] <= moments[-1]*1e-12:
        raise ValueError('本例只报告非线性转子的三个有限常数')
    hz = h/(8*np.pi**2*moments*atomic_mass*1e-20)
    return {'principal_moments_u_A2': moments.tolist(), 'ABC_MHz': (hz/1e6).tolist(),
            'ABC_cm-1': (hz/(100*c)).tolist()}


def audit_mol2(path):
    """单体系、显式 SYBYL 元素类型的保守检查；只读，不修复任意 MOL2。"""
    sections = {}
    current = None
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('@<TRIPOS>'):
            current = line[len('@<TRIPOS>'):]
            if current in sections:
                raise ValueError('本检查器不处理重复段或多分子文件')
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
        else:
            raise ValueError('段外存在未识别数据')
    header = sections.get('MOLECULE', [])
    if len(header) < 4:
        raise ValueError('缺少分子名、计数、分子类型或电荷类型')
    counts = list(map(int, header[1].split()))
    if len(counts) < 2 or counts[0] <= 0 or counts[1] < 0:
        raise ValueError('本检查器要求显式原子数与键数')
    atom_lines, bond_lines = sections.get('ATOM', []), sections.get('BOND', [])
    if len(atom_lines) != counts[0] or len(bond_lines) != counts[1]:
        raise ValueError('声明计数与 ATOM/BOND 实际行数不一致')
    atoms = []
    for line in atom_lines:
        cols = line.split()
        if len(cols) < 6:
            raise ValueError('原子行至少需要编号、名称、三坐标和类型')
        xyz = np.array(cols[2:5], dtype=float)
        element = cols[5].split('.')[0]
        if element not in atomic_numbers or element == 'X':
            raise ValueError('本检查器不猜测外部力场类型、通配符或虚拟粒子的元素')
        if not np.isfinite(xyz).all():
            raise ValueError('坐标必须有限')
        charge = None
        if header[3] != 'NO_CHARGES':
            if len(cols) < 9:
                raise ValueError('已声明电荷模型，但缺少子结构占位或电荷列')
            charge = float(cols[8])
            if not np.isfinite(charge):
                raise ValueError('电荷必须有限')
        atoms.append({'id': int(cols[0]), 'name': cols[1], 'element': element,
                      'xyz_A': xyz.tolist(), 'type': cols[5], 'charge_e': charge})
    ids = [a['id'] for a in atoms]
    if len(set(ids)) != len(ids) or min(ids) <= 0:
        raise ValueError('原子编号必须唯一且为正')
    allowed_bonds = {'1', '2', '3', 'ar', 'am', 'du', 'un', 'nc'}
    bonds = []
    for line in bond_lines:
        cols = line.split()
        if len(cols) < 4:
            raise ValueError('键行缺少编号、端点或类型')
        number, a, b = map(int, cols[:3])
        if a not in ids or b not in ids or a == b or cols[3] not in allowed_bonds:
            raise ValueError('键端点或键类型无效/不在检查范围内')
        bonds.append({'id': number, 'a': a, 'b': b, 'type': cols[3]})
    if len({b['id'] for b in bonds}) != len(bonds):
        raise ValueError('键编号重复')
    cell = None
    if 'CRYSIN' in sections:
        data = sections['CRYSIN']
        if len(data) != 1 or len(data[0].split()) != 8:
            raise ValueError('本例 CRYSIN 要求六个晶胞参数及空间群号、setting，空白分隔')
        vals = data[0].split()
        parameters = np.array(vals[:6], dtype=float)
        group, setting = map(int, vals[6:])
        if not np.isfinite(parameters).all() or np.any(parameters[:3] <= 0) or np.any(parameters[3:] <= 0) or np.any(parameters[3:] >= 180):
            raise ValueError('晶胞参数无效')
        if not 1 <= group <= 230 or setting < 1:
            raise ValueError('空间群号或 setting 无效')
        cell = Cell.fromcellpar(parameters)
        if cell.volume <= 0:
            raise ValueError('晶胞体积必须为正')
    return {'atoms': atoms, 'bonds': bonds, 'charge_type': header[3],
            'charge_sum_e': None if header[3] == 'NO_CHARGES' else sum(a['charge_e'] for a in atoms),
            'sequential_ids_from_one': ids == list(range(1, len(ids)+1)),
            'cell_volume_A3': None if cell is None else cell.volume}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True, help='尚不存在的输出目录')
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text())
    cm5 = data['CM5']
    xyz = np.array(cm5['coordinates_Angstrom'])
    q = np.array(cm5['charges_e'])
    cell = np.array([[7., 0., 0.], [1.5, 8., 0.], [.7, 1.2, 9.]])
    atoms = Atoms(cm5['elements'], positions=xyz, cell=cell, pbc=[True, False, True])
    atoms.new_array('charges', q)
    atoms.new_array('atom_id', np.array([101, 102, 103]))
    atoms.info.update(geometry='Gas-phase optimized water; artificial cell for format demonstration',
                      coordinate_unit='angstrom', charge_model='CM5', energy_unit='eV')
    # ASE 的 energy 字段用 eV；原始量化输出为 Hartree，显式换算。
    from ase.units import Hartree
    atoms.calc = SinglePointCalculator(atoms, energy=data['models']['water-opt']['final_energy_Hartree']*Hartree)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    out = args.output_dir
    write(out/'water.extxyz', atoms, format='extxyz', columns=['symbols', 'positions', 'charges', 'atom_id'])
    # ASE 写入器会把 species/pos 重新放到最前；手写一份合法异序模式以检查读取。
    header = 'Lattice="'+' '.join(str(v) for v in cell.ravel())+'" Properties=species:S:1:atom_id:I:1:charge:R:1:pos:R:3 pbc="T F T" charge_model=CM5'
    reordered_lines = ['3', header]
    for i, (s, r, charge) in enumerate(zip(cm5['elements'], xyz, q)):
        reordered_lines.append(f'{s} {101+i} {charge:.10f} {r[0]:.12f} {r[1]:.12f} {r[2]:.12f}')
    (out/'reordered.extxyz').write_text('\n'.join(reordered_lines)+'\n')
    loaded = read(out/'water.extxyz', format='extxyz')
    reordered = read(out/'reordered.extxyz', format='extxyz')
    for a in [loaded, reordered]:
        assert np.allclose(a.positions, xyz, atol=6e-9)
        assert np.allclose(a.cell, cell) and np.array_equal(a.pbc, [True, False, True])
        assert np.array_equal(a.arrays['atom_id'], [101, 102, 103])
        assert np.allclose(a.get_charges(), q, atol=6e-9)
    write(out/'water-plain.xyz', atoms, format='xyz', comment='Coordinates only; angstrom; metadata intentionally omitted')
    plain = read(out/'water-plain.xyz', format='xyz')
    assert np.allclose(plain.positions, xyz) and not plain.pbc.any()

    rows = ['@<TRIPOS>MOLECULE', 'water_cm5_geometry', '3 2 1 0 0', 'SMALL', 'USER_CHARGES',
            '@<TRIPOS>ATOM']
    for i, (s, r, charge) in enumerate(zip(cm5['elements'], xyz, q), 1):
        atom_type = 'O.3' if s == 'O' else 'H'
        rows.append(f'{i} {s}{i} {r[0]:.12f} {r[1]:.12f} {r[2]:.12f} {atom_type} 1 WAT {charge:.10f}')
    rows += ['@<TRIPOS>BOND', '1 1 2 1', '2 1 3 1', '@<TRIPOS>SUBSTRUCTURE', '1 WAT 1']
    (out/'water.mol2').write_text('\n'.join(rows)+'\n')
    cellpar = Cell(cell).cellpar()
    (out/'water-cell.mol2').write_text('\n'.join(rows+['@<TRIPOS>CRYSIN', ' '.join(f'{v:.12f}' for v in cellpar)+' 1 1'])+'\n')
    mol2 = audit_mol2(out/'water.mol2')
    mol2cell = audit_mol2(out/'water-cell.mol2')

    h_masses = [15.99491461957, 1.00782503223, 1.00782503223]
    d_masses = [15.99491461957, 2.01410177812, 2.01410177812]
    results = {'software': {'ase': ase.__version__},
               'source_sha256': {str(SOURCE.relative_to(ROOT)): hashlib.sha256(SOURCE.read_bytes()).hexdigest()},
               'geometry_level': cm5['level'], 'coordinate_unit': 'angstrom',
               'CM5_definition': cm5['source'],
               'format_example': {'cell_vectors_rows_A': cell.tolist(), 'cell_volume_A3': float(np.linalg.det(cell)),
                                  'pbc': [True, False, True], 'scope': 'Artificial cell; no water crystal or periodic electronic structure calculation.',
                                  'extxyz_columns_reordered_correctly_read': True,
                                  'plain_xyz_loses': ['cell', 'pbc', 'charges', 'atom_id', 'energy'],
                                  'extxyz_energy_eV': loaded.get_potential_energy(),
                                  'mol2_crysin_scope': 'Full periodic cell metadata; not the partial pbc of the extxyz example; no symmetry expansion inferred.'},
               'mol2': mol2, 'mol2_with_cell': mol2cell,
               'rigid_rotor_same_geometry': {'H2O_masses_u': h_masses, 'D2O_masses_u': d_masses,
                                             'H2O': rotational_constants(xyz, h_masses),
                                             'D2O': rotational_constants(xyz, d_masses),
                                             'scope': 'Same equilibrium electronic geometry, rigid rotor only; no vibrational averaging, experimental fit, or isotope geometry correction.'}}
    (out/'analysis.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps({'cell_volume_A3': results['format_example']['cell_volume_A3'],
                      'mol2_charge_sum_e': mol2['charge_sum_e'],
                      'H2O_ABC_MHz': results['rigid_rotor_same_geometry']['H2O']['ABC_MHz'],
                      'D2O_ABC_MHz': results['rigid_rotor_same_geometry']['D2O']['ABC_MHz']}))


if __name__ == '__main__':
    main()
