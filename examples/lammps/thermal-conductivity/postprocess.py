"""用法：python3 postprocess.py；读取两个 LAMMPS 日志与 profile 文件，写 results.json 和 result.png。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DT = 0.005
NPROD_EMD = 100000
NPROD_NEMD = 40000


def need(path):
    if not Path(path).exists():
        raise SystemExit(f"缺少 {path}，请先运行 run.py")


for name in ("log.emd", "log.nemd", "profile.heatflux", "profile.nemd"):
    need(name)
for name in ("log.emd", "log.nemd"):
    if "Total wall time:" not in Path(name).read_text():
        raise SystemExit(f"{name} 未正常结束")


def number(text):
    return float(text.replace("D", "E").replace("d", "e"))


def read_correlate(path):
    """读取 fix ave/correlate 的最后一个运行平均块。"""
    lines = [line for line in Path(path).read_text().splitlines() if line and not line.startswith("#")]
    blocks = []
    i = 0
    while i < len(lines):
        head = lines[i].split()
        i += 1
        if len(head) != 2:
            raise SystemExit(f"{path} 的相关块头格式异常")
        count = int(head[1])
        rows = []
        for _ in range(count):
            rows.append([number(v) for v in lines[i].split()])
            i += 1
        blocks.append(np.array(rows))
    if not blocks:
        raise SystemExit(f"{path} 没有可用数据")
    return blocks[-1]


def read_profile(path):
    """读取 fix ave/chunk 的最后一个温度剖面块。"""
    blocks = {}
    current = None
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            current = int(parts[0])
            blocks[current] = []
        elif current is not None and len(parts) == 4 and parts[0].isdigit():
            blocks[current].append([number(v) for v in parts])
    if not blocks:
        raise SystemExit(f"{path} 没有可用剖面")
    step = max(blocks)
    return step, np.array(blocks[step])


# EMD：日志中的末值与相关函数积分应互相核对。
log_emd = Path("log.emd").read_text()
match = re.search(r"(?m)^EMD_RESULT\s+(\S+)\s+(\S+)$", log_emd)
if not match:
    raise SystemExit("log.emd 中未找到 EMD_RESULT")
kappa_emd, volume = number(match.group(1)), number(match.group(2))
thermo = []
for line in log_emd.splitlines():
    parts = line.split()
    if len(parts) == 9 and parts[0].isdigit():
        thermo.append([number(v) for v in parts])
if not thermo:
    raise SystemExit("log.emd 中没有热力学输出")
last = thermo[-1]
temperature = last[1]
components = last[5:8]

corr = read_correlate("profile.heatflux")
lag = corr[:, 1] * DT
weight = corr[:, 2]
if np.any(weight <= 0):
    raise SystemExit("相关函数计数异常")
acf = corr[:, 3:6]
running = np.vstack(
    [
        np.zeros(3),
        np.cumsum((acf[1:] + acf[:-1]) * np.diff(lag)[:, None] / 2, axis=0),
    ]
)
running_kappa = running / (volume * temperature**2)
kappa_profile = running_kappa[-1]
if abs(kappa_profile.mean() - kappa_emd) > 0.05 * max(kappa_emd, 1):
    raise SystemExit("相关函数积分与日志末值不一致，请检查单位与体积")

# NEMD：日志给出生产段累积交换能与平均温差，剖面用于检查线性。
log_nemd = Path("log.nemd").read_text()
match = re.search(r"(?m)^NEMD_RESULT\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$", log_nemd)
if not match:
    raise SystemExit("log.nemd 中未找到 NEMD_RESULT")
energy, delta_t, kappa_nemd, lx, ly, lz, t_end = [number(v) for v in match.groups()]
area = lx * ly
production_time = NPROD_NEMD * DT
kappa_check = (energy / (production_time * area) / 2) * (lz / 2) / delta_t

step, profile = read_profile("profile.nemd")
z = profile[:, 1]
temp = profile[:, 3]
# 中心热层相对两端平均温度的超出量，用来判断剖面是否接近线性响应。
center_excess = float(temp[10] - 0.5 * (temp[0] + temp[-1]))

result = {
    "state_point": {
        "density_reduced": 0.6,
        "temperature_reduced": 1.35,
        "cutoff_reduced": 2.5,
    },
    "emd": {
        "atoms": 4000,
        "production_steps": NPROD_EMD,
        "production_time_reduced": NPROD_EMD * DT,
        "correlation_time_reduced": lag[-1],
        "temperature_reduced": temperature,
        "volume_reduced": volume,
        "kappa_reduced": kappa_emd,
        "kappa_components_reduced": list(components),
        "kappa_from_profile_reduced": float(kappa_profile.mean()),
    },
    "nemd": {
        "atoms": 8000,
        "production_steps": NPROD_NEMD,
        "production_time_reduced": production_time,
        "energy_delta_reduced": energy,
        "temperature_difference_reduced": delta_t,
        "area_reduced": area,
        "length_z_reduced": lz,
        "kappa_reduced": kappa_nemd,
        "kappa_from_global_flux_reduced": kappa_check,
        "center_excess_reduced": center_excess,
        "profile_step": step,
    },
    "reference": {
        "kappa_reduced": 3.4,
        "source": "Evans, Phys. Rev. A 34, 1449 (1986); LAMMPS examples/KAPPA/README",
    },
}
result["difference"] = {
    "emd_vs_reference_percent": 100 * (kappa_emd / 3.4 - 1),
    "nemd_vs_reference_percent": 100 * (kappa_nemd / 3.4 - 1),
    "emd_vs_nemd_percent": 100 * (kappa_emd / kappa_nemd - 1),
}

fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.8), layout="constrained")
for i, label in enumerate(("x", "y", "z")):
    axs[0].plot(lag, running_kappa[:, i], alpha=0.45, label=label)
axs[0].plot(lag, running_kappa.mean(axis=1), color="black", label="mean")
axs[0].axhline(3.4, color="tab:red", ls="--", lw=1, label="reference 3.4")
axs[0].set(xlabel="Integration limit (τ)", ylabel="Running κ (ε/(τσ))", title="EMD: Green–Kubo")
axs[0].legend(frameon=False, ncol=2)

axs[1].plot(z, temp, "o-", ms=3, lw=0.8, label="profile")
axs[1].axhline(temp.mean(), color="gray", ls=":", lw=1, label="mean T")
axs[1].annotate(
    f"center excess {center_excess:.2f}",
    xy=(z[10], temp[10]),
    xytext=(0.55, 0.25),
    textcoords="axes fraction",
    arrowprops={"arrowstyle": "->", "lw": 0.8},
    fontsize=8,
)
axs[1].set(xlabel="z / Lz", ylabel="T (ε/kB)", title="NEMD: temperature profile")
axs[1].legend(frameon=False, fontsize=8)

fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
