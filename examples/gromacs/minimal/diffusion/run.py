"""用法：python3 run.py；GMX_EXEC 指定串行/thread-MPI gmx，默认2线程。"""

import os
import shutil
import subprocess
from pathlib import Path

if Path("em.tpr").exists():
    raise SystemExit("已有计算输出，请使用干净的案例目录")

MODE = "diffusion"
exe = shutil.which(os.environ.get("GMX_EXEC", "gmx"))
if exe is None:
    raise SystemExit("找不到 gmx")
threads = os.environ.get("GMX_THREADS", "2")


# 每阶段单独保留日志，不用 -maxwarn 跳过输入检查。
def stage(name, coordinate, checkpoint=None):
    command = [
        exe,
        "grompp",
        "-f",
        name + ".mdp",
        "-c",
        coordinate,
        "-p",
        "topol.top",
        "-o",
        name + ".tpr",
        "-po",
        name + "-processed.mdp",
    ]
    if checkpoint:
        command += ["-t", checkpoint]
    with Path(name + "-grompp.log").open("w") as out:
        subprocess.run(command, stdout=out, stderr=subprocess.STDOUT, check=True)
    with Path(name + "-mdrun.log").open("w") as out:
        subprocess.run(
            [exe, "mdrun", "-deffnm", name, "-ntmpi", "1", "-ntomp", threads],
            stdout=out,
            stderr=subprocess.STDOUT,
            check=True,
        )


stage("em", "structure.gro")
if MODE != "energy-minimization":
    stage("nvt", "em.gro")
if MODE == "npt":
    stage("npt", "nvt.gro", "nvt.cpt")
if MODE == "diffusion":
    stage("md", "nvt.gro", "nvt.cpt")
