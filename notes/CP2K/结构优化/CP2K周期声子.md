# CP2K 周期声子

**适用环境：CP2K 2026.2，Alkemie 后端环境中的 Phonopy。**

## 一、生成位移超胞并计算受力

从充分弛豫的三维周期结构出发，Phonopy 会根据晶体对称性自动挑选需要施加正负位移的原子，Alkemie 则为每个位移构型生成对应的 CP2K 单点受力输入。每个位移分支中，晶胞参数和其余原子坐标均保持固定；计算完成后，请保留各分支的原始输入和输出文件。

```bash
PYTHONPATH=backend python scripts/cp2k_phonon.py prepare relaxed.extxyz phonon --supercell 2 2 2
```

## 二、汇总力常数、色散和态密度

准备好以倒易分数坐标表示的 q 点路径序列（例如 `[[0,0,0],[0.5,0.5,0]]`，具体高对称点需按所用原胞确定）。运行汇总脚本时，程序会逐个分支核对原子坐标、原子顺序以及受力收敛情况，将 CP2K 的受力单位从 Ha/bohr 换算为 eV/Å，并扣除每个超胞中的残余整体净力：

```bash
PYTHONPATH=backend python scripts/cp2k_phonon.py collect phonon --mesh 12 12 12 --path qpoints.json
```

运行后会生成 `phonopy.yaml`、`band.yaml` 和 `total_dos.dat`。分析结果时，应先检查 Γ 点的三条声学模频率是否接近零，再逐步检验超胞尺寸、位移幅值和 CP2K 截断能的收敛性。如果研究的是极性晶体，计算 LO–TO 分裂还需额外提供 Born 有效电荷与介电张量。

## 三、最小运行检查

我们在本机对两原子 Si 原胞施加 0.01 Å 位移，运行了两个独立的 CP2K 受力分支。Phonopy 成功给出了 Γ 点三条近零声学模，并输出了声子色散与总态密度。需要说明的是，1×1×1 超胞仅用于验证数据衔接流程；若要获得定量的声子频率，还需扩大超胞并重新做收敛性测试。
