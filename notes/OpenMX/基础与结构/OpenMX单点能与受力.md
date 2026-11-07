# OpenMX 单点能与受力

**适用环境：Linux + PBS 运行计算；Windows / macOS / Linux 可准备结构与分析结果。**

OpenMX 单点计算在给定结构上求解电子态，并计算能量与受力。它是测试基组、网格和磁态的起点。

本例用键长 1 Å 的中性 H₂ 练习单点计算，放入 10 Å 立方盒，采用 GGA-PBE、H5.0-s2p1 基组、H_PBE19 赝势与 `Cluster` 求解器。每个 H 的初始上下自旋电子数各为 0.5，对应闭壳层初猜。

## 准备并运行 H₂ 案例

[最小案例](../../../examples/openmx/minimal/single-point)包含：

- [system.dat](../../../examples/openmx/minimal/single-point/system.dat)
- [structure.xyz](../../../examples/openmx/minimal/single-point/structure.xyz)
- [run.py](../../../examples/openmx/minimal/single-point/run.py)：组织计算步骤。
- [job.pbs](../../../examples/openmx/minimal/single-point/job.pbs)：单节点 PBS 作业。
- [postprocess.py](../../../examples/openmx/minimal/single-point/postprocess.py)：检查并提取结果。
- [requirements.txt](../../../examples/openmx/minimal/single-point/requirements.txt)：Python 分析依赖。

在集群加载 OpenMX，并将 `OPENMX_DATA` 设为安装中的 `DFT_DATA19` 目录；其中应包含所选 PAO 和 VPS。势与基组由安装提供，案例不附带这些数据。`run.py` 将输入中的 `@DATA_PATH@` 替换为该目录，生成 `runtime.dat`；结构和电子参数均来自 `system.dat`。

在案例目录安装 Python 依赖并提交：

```bash
python3 -m pip install -r requirements.txt
qsub job.pbs
```

作业结束后会自动执行后处理。重新分析已有输出时，可单独运行 `python3 postprocess.py`。PBS 中的软件加载方式与资源语法按集群配置调整；此例不需要多节点。

## 基组、网格和电子收敛

| 设置 | 本例 | 物理/数值含义 |
| --- | --- | --- |
| PAO | `H5.0-s2p1` | 5 bohr 截断半径、两套 s 与一套 p 径向函数 |
| `scf.energycutoff` | 200 Ry | 积分网格，不是平面波轨道截断 |
| `scf.criterion` | 1e−8 Hartree | 电子求解标准，另检查迭代历史 |
| `MD.Type` | `nomd` | 不移动原子 |

局域基组半径、轨道数量和网格应分别测试；增加网格不能弥补轨道表达能力不足。

## 单点计算有受力正常吗

检查 `openmx.out` 是否正常结束，再查看 `system.out` 中的 SCF 过程、总能 `Utot` 和最终坐标受力表。本例电子总能约 −1.13309142 Hartree。

单点计算固定的是原子位置，不要求受力为零。本例的 H—H 距离尚未优化，因此存在受力是正常的；后续可以用[几何优化](OpenMX几何优化.md)寻找平衡键长。

后处理检查 SCF 最终密度残差并提取总能。若需要电荷或轨道分析，可按官方格式输出网格/轨道，再使用 OpenMX Viewer、VESTA 或支持该格式的分析工具；不同分区的局域电荷不应混用。

换成周期晶体时应同时修改晶格、求解器和 k 网格；不能仅把原子坐标替换后继续沿用孤立分子设置。

进一步了解方法与文件规则，可看[OpenMX 基础知识](OpenMX基础知识.md)。参考：[OpenMX 4.0 输入与输出手册](https://openmx-square.org/openmx_man4.0/s8_2_keywords.html)。
