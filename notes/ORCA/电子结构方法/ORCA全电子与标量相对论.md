# ORCA 全电子与标量相对论

**适用环境：Linux + PBS 运行计算；Windows / macOS / Linux 可准备输入与分析结果。**

全电子计算显式处理芯电子与价电子，适合讨论芯区性质、核相关光谱与重元素的相对论效应。全电子是电子表示方式，不能直接等同于“所有性质都更准确”。

## 全电子、ECP 与 X2C 各自表示什么

赝势/ECP 以有效算符替代一部分芯电子，全电子基组则显式描述全部电子。使用 ECP 时必须配套相容价电子基组；做全电子时还需选择适合所用哈密顿量的芯区基函数。

X2C 从相对论理论构造有效电子哈密顿量。ORCA 本例的 X2C 是**标量相对论的一分量实现**，不等于已经包含两分量 SOC，也不能把基组名中的 “2c” 当作启用 SOC 的开关。核模型、基组收缩和性质算符的 picture-change 处理也影响重元素结果。

## 对同一 Ar 原子改变哈密顿量

以 Ar 原子为例，使用同一 `x2c-SVPall` 全电子基组，分别运行非相对论 HF 与 HF-X2C。两者均为中性闭壳层、18 个显式电子，没有使用 ECP；固定基组便于识别哈密顿量变化。该基组针对 X2C 设计，非相对论结果只作同基组对照。

[案例目录](../../../examples/orca/minimal/all-electron-x2c)包含以下科学输入：

[nonrel.inp](../../../examples/orca/minimal/all-electron-x2c/nonrel.inp)、[stages.json](../../../examples/orca/minimal/all-electron-x2c/stages.json)、[structure.xyz](../../../examples/orca/minimal/all-electron-x2c/structure.xyz)、[x2c.inp](../../../examples/orca/minimal/all-electron-x2c/x2c.inp)。

结构写在坐标文件或各输入的原子/晶胞段；`stages.json` 列出计算阶段。配套 [run.py](../../../examples/orca/minimal/all-electron-x2c/run.py) 顺序组织任务，[job.pbs](../../../examples/orca/minimal/all-electron-x2c/job.pbs) 提交作业，[postprocess.py](../../../examples/orca/minimal/all-electron-x2c/postprocess.py) 检查结果并绘图。

## 运行两个 HF 分支

加载 ORCA 及其匹配的 MPI 环境，`ORCA_EXEC` 可指定驱动绝对路径。每步使用一个进程和 1000 MB 主要工作区，驱动外不加 `mpirun`；基组来自程序安装。

| 设置 | 判断依据 |
| --- | --- |
| `HF` | 将演示集中在哈密顿量，不混入泛函变化 |
| `x2c-SVPall` | 全电子相对论基组；更大体系应测试三/四 zeta |
| `X2C` | 只在相对论分支启用，核对原生输出 |
| `0 1` | Ar 中性单重态；其他元素需重新确定电子态 |

这里没有以更多进程换速度，小原子的启动与积分开销可能占主导。

在干净案例目录安装[Python 依赖](../../../examples/orca/minimal/all-electron-x2c/requirements.txt)并提交：

```bash
python3 -m pip install -r requirements.txt
qsub job.pbs
```

PBS 中的资源语法和软件加载方式按集群调整。计算结束后自动执行后处理；若只分析已保存的结果，运行 `python3 postprocess.py`。各阶段独立保存输出，便于定位失败步骤。

## 总能差不等于化学键能

后处理核对两分支显式电子数均为 18，且相对论分支实际启用 X2C。非相对论与 X2C 总能分别约 −526.35728314 与 −528.41261477 Hartree，相差约 −2.05533163 Hartree。

这两个总能描述的是同一原子的全部芯/价电子对哈密顿量变化的响应。该差值并不对应某条化学键的相对论贡献，也不能直接加到其他分子的反应能上。研究化学问题时，应在一致理论层级下分别计算各物种，再构造所需能量差。

## 扩展到实际研究

反应能、结构、NMR/EPR 等目标需要分别检查泛函/相关方法、基组、相对论与核模型。全电子表示并不要求在相关计算中关联所有芯电子，参见[电子关联与冻结核](ORCA电子关联与冻结核.md)。轨道和密度可通过 `orca_2mkl` 转为 Multiwfn 支持格式，但核相关性质应优先使用程序原生响应模块。

参考：[ORCA 相对论章节](https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/relativistic.html)。
