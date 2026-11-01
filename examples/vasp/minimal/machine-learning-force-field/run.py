"""用法：python3 run.py [--ranks 2]；短程训练、重拟合、独立构型预测与 DFT 对照。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    if args.ranks < 1:
        parser.error("MPI 进程数须为正整数")
    root = Path.cwd()
    if not (root / "POTCAR").is_file():
        raise SystemExit("请先准备授权 Si POTCAR")
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    for mode in ["train", "refit", "run", "reference"]:
        work = root / mode
        if work.exists():
            raise SystemExit(f"{mode} 已存在，请在新目录运行或只做后处理")
        work.mkdir()
        shutil.copy2(root / f"INCAR.{mode}", work / "INCAR")
        shutil.copy2(
            root / ("POSCAR" if mode in ["train", "refit"] else "POSCAR.test"),
            work / "POSCAR",
        )
        for name in ["POTCAR", "KPOINTS"]:
            shutil.copy2(root / name, work / name)
        if mode == "refit":
            shutil.copy2(root / "train/ML_ABN", work / "ML_AB")
        elif mode == "run":
            shutil.copy2(root / "refit/ML_FFN", work / "ML_FF")
        with (work / "vasp.log").open("w") as log:
            subprocess.run(
                command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
            )
        text = (work / "OUTCAR").read_text(errors="replace")
        if "General timing and accounting" not in text:
            raise SystemExit(f"{mode} 未正常结束")
        if mode == "train" and not (work / "ML_ABN").is_file():
            raise SystemExit("未生成训练数据库，请检查 ML_LOGFILE 的训练状态")
        if mode == "refit" and not (work / "ML_FFN").is_file():
            raise SystemExit("未生成重拟合力场，请检查 ML_LOGFILE")
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
