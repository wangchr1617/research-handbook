"""用法：python3 prepare.py；调用 Multiwfn，以 structure.xyz 生成 cp2k.inp。"""

import os
import shutil
import subprocess
from pathlib import Path


def main():
    executable = os.environ.get(
        "MULTIWFN_EXEC"
    )  # 可设为本机 Multiwfn 的程序名或绝对路径。
    if not executable:
        executable = next(
            (
                name
                for name in ("Multiwfn", "Multiwfn_noGUI", "multiwfn")
                if shutil.which(name)
            ),
            None,
        )
    if not executable:
        raise SystemExit("请安装 Multiwfn，或设置 MULTIWFN_EXEC")
    target = Path("cp2k.inp")
    if target.exists():
        raise SystemExit("cp2k.inp 已存在；如需重新生成，请先移走该文件")
    with Path("multiwfn.in").open() as commands, Path("multiwfn.log").open("w") as log:
        subprocess.run(
            [executable, "structure.xyz"],
            stdin=commands,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    if not target.is_file() or "&GLOBAL" not in target.read_text():
        raise SystemExit("未生成有效输入，请检查 multiwfn.log")
    print("已生成 cp2k.inp，请检查周期性、库文件名及收敛参数")


if __name__ == "__main__":
    main()
