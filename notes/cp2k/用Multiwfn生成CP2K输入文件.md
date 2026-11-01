# 用 Multiwfn 生成 CP2K 输入文件

**适用环境：Windows、macOS、Linux（准备输入）；Linux + PBS（提交计算）。**

Multiwfn 可以读取 XYZ、CIF 等结构文件，生成单点、结构优化、分子动力学等 CP2K 输入。先用菜单搭好计算方案，再检查生成文件，比从零手写更方便。本篇以孤立水分子为例；晶体计算需保留真实晶胞和周期性。

## 准备结构与工具

从 [Multiwfn 官网](http://sobereva.com/multiwfn) 获取适合系统的版本。Windows 可运行图形界面版本，macOS、Linux 可使用命令行版本；不同安装方式的程序名可能是 `Multiwfn`、`Multiwfn_noGUI` 或 `multiwfn`。

将案例中的 [structure.xyz](../../examples/cp2k/minimal/multiwfn-input/structure.xyz) 放到工作目录，启动程序并载入该文件。命令行示例：

```bash
Multiwfn structure.xyz
```

## 生成水分子单点输入

在主菜单输入 `cp2k`，输出文件名填 `cp2k.inp`。随后依次设置：

| 菜单项 | 本例选择 | 含义 |
| --- | --- | --- |
| `-7` | `NONE` | 水分子为孤立体系 |
| `1` | 保持 PBE | 交换关联泛函 |
| `2` | 保持 DZVP-MOLOPT-SR-GTH | 基组与配套赝势 |
| `4` | 切换为 OT | 本例为闭壳层、无 k 点采样的分子 |
| `0` | 生成文件 | 写出 CP2K 输入 |
| `-10`、`q` | 返回并退出 | 完成准备 |

菜单名称比编号更可靠，软件更新后以屏幕提示为准。本例提供了可检查、可复用的 [multiwfn.in](../../examples/cp2k/minimal/multiwfn-input/multiwfn.in)，也可用 [prepare.py](../../examples/cp2k/minimal/multiwfn-input/prepare.py) 调用 Multiwfn：

```bash
python3 prepare.py
```

本例生成的 [cp2k.inp](../../examples/cp2k/minimal/multiwfn-input/cp2k.inp) 使用非周期边界与 WAVELET 泊松求解器，并将分子居中。盒长约 8.514 Å；正式计算应检查盒长、`CUTOFF`、`REL_CUTOFF` 和基组收敛，而非直接照搬默认值。

## 检查输入并提交 PBS

打开 `cp2k.inp`，重点核对：

- `&CELL/PERIODIC` 与 `&POISSON/PERIODIC` 是否符合模型。三维晶体通常为 `XYZ`，孤立分子为 `NONE`。
- `BASIS_SET_FILE_NAME`、`POTENTIAL_FILE_NAME` 能否从集群的 CP2K 数据目录找到。本例生成器写出的是 `BASIS_MOLOPT` 和 `POTENTIAL`；案例不附带这些库文件。
- 元素、净电荷、自旋多重度、泛函和基组是否符合体系。OT 适合有带隙且固定占据的体系；金属或需要展宽时考虑对角化与混合方案。

将输入及 [job.pbs](../../examples/cp2k/minimal/multiwfn-input/job.pbs)、[postprocess.py](../../examples/cp2k/minimal/multiwfn-input/postprocess.py) 放在集群同一目录，按集群说明加载 CP2K 环境，然后提交：

```bash
qsub job.pbs
```

作业结束后检查 `cp2k.out` 中的 SCF 收敛与正常结束标记。`postprocess.py` 仅汇总能量和完成状态，便于快速核对；计算方案仍由 Multiwfn 生成的输入决定。

## 换成其他任务

在 `-1` 菜单选择任务名称即可生成不同骨架：`Energy + force` 为能量与受力，`Optimizing structure` 优化原子位置，`Optimizing both structure and cell` 还优化晶胞，`Molecular dynamics` 生成分子动力学输入。任务改变后，优化算法、外压、温度和时间步长等菜单也会变化。

需要分析电子结构时，可通过 `-2` 开启 Molden 输出，通过 `-3` 配置 Cube 输出，再交给 Multiwfn 做波函数或网格分析。是否能使用某项分析取决于输出是否包含所需信息；仅有结构文件不能代替波函数。

发表研究时，按 [Multiwfn 官网](http://sobereva.com/multiwfn) 的要求引用程序论文，并在方法部分说明其用途。
