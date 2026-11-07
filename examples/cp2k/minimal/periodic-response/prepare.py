"""准备周期波函数分析副本；用法：python prepare.py work/periodic-tddfpt/optical-MOS-1_0.molden work。"""
import argparse
import re
from pathlib import Path


def prepare(source, target):
    text = source.read_text()
    # 本例限定 O q6/H q1；其他体系从实际赝势重新建立映射。
    if '[Nval]' in text:
        raise ValueError('请使用 CP2K 原始导出文件')
    if not re.search(r'\[Cell\]', text) or not re.search(r'\[Pseudo\]', text):
        raise ValueError('需要晶胞与逐原子赝势信息')
    pseudo = re.search(r'\[Pseudo\]([^\[]+)', text).group(1).splitlines()
    rows = [line.split() for line in pseudo if line.strip()]
    if len(rows) != 6 or any(row[0] not in {'O', 'H'} or int(row[2]) != {'O': 6, 'H': 1}[row[0]] for row in rows):
        raise ValueError('此脚本只适用于本例的两分子 O q6/H q1 模型')
    text = text.replace('[GTO]', '[Nval]\nO 6\nH 1\n[GTO]', 1)
    here = Path(__file__).parent
    for label in ['grid', 'translated', 'igmh', 'igmh-translated', 'grid-fine', 'igmh-fine', 'nto']:
        folder = target / label
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'periodic.molden').write_text(text)
        (folder / 'input.txt').write_text((here / (label + '.in')).read_text())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    prepare(args.source, args.target)
