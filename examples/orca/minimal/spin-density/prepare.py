"""分阶段准备拉伸H2计算；python prepare.py scf|post|natural --work-root WORK。"""
import argparse
from pathlib import Path
import shutil


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['scf','post','natural']);p.add_argument('--work-root',type=Path,required=True);a=p.parse_args();src=Path(__file__).resolve().parent;work=a.work_root;jobs=[]
    if a.stage=='scf':
        for mode in ['rhf','hs','bs']:jobs.append((mode,[(src/f'{mode}.inp','orca.inp'),(src/'structure.xyz','structure.xyz')],None))
    elif a.stage=='post':
        for mode in ['rhf','hs','bs']:
            if 'ORCA TERMINATED NORMALLY' not in (work/mode/'orca.out').read_text():raise ValueError('前序ORCA未正常结束')
            f=work/mode/'orca.molden.input'
            jobs.append((f'{mode}-export',[(f,'orca.molden.input')],'100\n2\n32\nmatrices.mwfn\n2\n2\n7\nscf.fch\n0\nq\n'))
            if mode!='rhf':
                for tag,menu in [('spin-grid','5\n5\n4\n.2\n2\n0\nq\n'),('rho-grid','5\n1\n4\n.2\n2\n0\nq\n'),('becke','15\n1\n5\n0\nq\n')]:jobs.append((f'{mode}-{tag}',[(f,'orca.molden.input')],menu))
    else:
        for mode in ['hs','bs']:
            for tag,number in [('UNO',1),('NSO',2),('SNO',3)]:jobs.append((f'{mode}-{tag}',[(work/f'{mode}-export/scf.fch','scf.fch')],f'200\n16\nSCF\n{number}\ny\n0\nq\n'))
    for tag,files,_ in jobs:
        if (work/tag).exists():raise FileExistsError(work/tag)
        for source,_ in files:
            if not source.is_file():raise FileNotFoundError(source)
    for tag,files,menu in jobs:
        d=work/tag;d.mkdir(parents=True)
        for source,name in files:shutil.copyfile(source,d/name)
        if menu is not None:(d/'input.txt').write_text(menu)


if __name__=='__main__':main()
