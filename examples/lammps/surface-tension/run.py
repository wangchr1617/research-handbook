#!/usr/bin/env python3
"""Run the LJ surface-tension input and build the summary figure."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LMP = os.environ.get("LMP_EXEC", "lmp")


def main() -> None:
    if shutil.which(LMP) is None:
        raise SystemExit(f"LAMMPS executable not found: {LMP}")
    subprocess.run([LMP, "-in", "in.surface", "-log", "log.surface"],
                   cwd=HERE, check=True)
    subprocess.run([sys.executable, "postprocess.py"], cwd=HERE, check=True)


if __name__ == "__main__":
    main()
