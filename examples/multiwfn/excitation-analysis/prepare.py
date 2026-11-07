"""准备水二聚体激发分析；用法：python prepare.py --wavefunction FILE --response FILE --output-dir WORK。"""
import argparse
import re
import shutil
from pathlib import Path



def menus(response):
    response = str(response.resolve())
    jobs = {}
    for n in [32, 48, 64]:
        jobs[f'hole-{n}'] = f'18\n1\n{response}\n3\n1\n4\n{15.117808996/n:.12f}\n10\n1\n11\n1\n12\n1\n12\n2\n13\n15\n0\n0\n0\nq\n'
    jobs['cross-32'] = f'18\n1\n{response}\n3\n1\n4\n{15.117808996/32:.12f}\n10\n3\n11\n3\n0\n0\n0\nq\n'
    jobs['orbitals-32'] = f'200\n3\n1-46\n4\n{15.117808996/32:.12f}\n1\n0\nq\n'
    jobs['matrices'] = '100\n2\n32\nmatrices.mwfn\n2\n0\nq\n'
    for state in [1, 2, 3]:
        jobs[f'nto-{state}'] = f'18\n6\n{response}\n{state}\n3\nnto.mwfn\n0\n0\nq\n'
    for name, method in [('ifct-mulliken', 1), ('ifct-hirshfeld', 2)]:
        jobs[name] = f'18\n8\n{method}\n{response}\n3\n2\n1-3\n4-6\n1\n-1\n0\nq\n'
    return jobs


def prepare(wavefunction, response, output):
    text = wavefunction.read_text()
    if not re.search(r'\[Nval\]\s+O 6\s+H 1', text):
        raise ValueError('需要已核对 O q6/H q1 的分析副本，见周期响应案例')
    cell = re.search(r'\[Cell\] Angs\s+([^\[]+)', text)
    if not cell or [float(x) for x in cell[1].split()] != [8.,0.,0.,0.,8.,0.,0.,0.,8.]:
        raise ValueError('此示例限定 8 Å 立方周期盒')
    occup = [float(x) for x in re.findall(r'Occup\s*=\s*(\S+)', text)]
    if occup != [2.]*8+[0.]*38:
        raise ValueError('此示例限定 46 空间轨道与 16 个显式电子')
    if output.exists():
        raise FileExistsError('选择新的工作目录，避免覆盖已有分析')
    output.mkdir(parents=True)
    for name, menu in menus(response).items():
        folder = output/name
        folder.mkdir()
        shutil.copyfile(wavefunction, folder/'periodic.molden')
        (folder/'input.txt').write_text(menu)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wavefunction', type=Path, required=True)
    parser.add_argument('--response', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.wavefunction, args.response, args.output_dir)
