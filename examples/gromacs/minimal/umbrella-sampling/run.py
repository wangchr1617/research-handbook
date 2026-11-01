"""用法：python3 run.py；原生GROMACS窗口采样，GMX_EXEC 指定thread-MPI入口。"""

import json
import os
import shutil
import subprocess
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "2"
CASE = "umbrella-sampling"
exe = shutil.which(os.environ.get("GMX_EXEC", "gmx"))
if not exe:
    raise SystemExit("找不到 GROMACS")
for stage in json.loads(Path("stages.json").read_text()):
    work = Path(stage)
    if work.exists():
        raise SystemExit(f"{stage} 已存在，请使用干净目录")
    work.mkdir()
    for ext in ["gro", "top", "mdp"] + (["ndx"] if CASE == "umbrella-sampling" else []):
        shutil.copy(stage + "." + ext, work / ("input." + ext))
    shutil.copy("em.mdp", work / "em.mdp")
    with (work / "driver.log").open("w") as out:

        def call(args, directory=work, log=out):
            subprocess.run(
                [exe] + args,
                cwd=directory,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )

        call(
            [
                "grompp",
                "-f",
                "em.mdp",
                "-c",
                "input.gro",
                "-p",
                "input.top",
                "-o",
                "em.tpr",
            ]
        )
        call(["mdrun", "-deffnm", "em", "-ntmpi", "1", "-ntomp", "2"])
        flags = ["-n", "input.ndx"] if CASE == "umbrella-sampling" else []
        call(
            [
                "grompp",
                "-f",
                "input.mdp",
                "-c",
                "em.gro",
                "-p",
                "input.top",
                "-o",
                "md.tpr",
            ]
            + flags
        )
        call(["mdrun", "-deffnm", "md", "-ntmpi", "1", "-ntomp", "2"])
