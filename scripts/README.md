# 科研脚本

按用途选择入口。Python 文件开头给出用途或用法；带命令行参数的工具可先运行 `python 脚本.py --help`。运行前核对输入格式、单位和依赖。

| 目录 | 用途 |
| --- | --- |
| [materials](materials/README.md) | 本机材料案例的输入生成、运行、检查与重绘 |
| [structure](structure/README.md) | 结构、轨迹与训练数据转换，分组和扰动 |
| [analysis](analysis/README.md) | 误差、键长、RDF、能量与电池性质分析 |
| [plotting](plotting/README.md) | MSD、声子能带与 NEP 描述符 PCA / 采样 |
| [vasp](vasp/README.md) | 批量任务准备、结果汇总与结构收集 |
| [cp2k](cp2k/README.md) | 重启输入更新、任务类型切换与结果分析 |
| [gpumd](gpumd/README.md) | GPUMD / NEP 工作流与结构优化 |
| [deepmd](deepmd/README.md) | 描述符和 DP-GEN 偏差数据 |
| [visualization](visualization/README.md) | Chemiscope 可视化输入 |
| [tools](tools/README.md) | 第三方科研工具包 |
| [utils](utils/README.md) | 通用 Shell 辅助脚本 |
| [backend](backend/README.md) | Agent 请求、状态恢复与 HTTP 工具并发练习 |
| [note-audit](note-audit/README.md) | Markdown 结构、中文排版与本地链接检查 |

通用文件清理与软链接操作见 [utils](utils/README.md)。绘图按数据格式和单位选择入口；任务专用绘图也可参考[科研数据读写与绘图](../notes/Python/科研数据读写与绘图.md)。

## 运行环境

建议 Python 3.10 及以上。常用数据处理依赖可按需要安装：

```bash
python -m pip install numpy scipy ase matplotlib pandas dpdata
```

NEP、声子、Raman 等专门计算还需各脚本使用的 Calorine / PyNEP、Phonopy / phono3py、DFTD3、GPUMD 等软件。CP2K 格式和任务切换工具依赖 Multiwfn，KPOINTS 批量生成依赖 VASPKIT，SQS 转换依赖 ATAT；这些程序需自行安装并配置路径。

输入模板见 [inputs](../inputs/README.md)。完整案例见 [examples](../examples/README.md)。模板中的集群路径与队列参数应按实际环境修改。

## 检查与测试

笔记检查使用 Node.js 22 或更新版本，安装与运行见 [note-audit](note-audit/README.md)。下面是 Python 科研脚本的检查方法。

```bash
python -m pip install pytest ruff
python -m pytest scripts/tests -q
ruff check scripts --exclude tools --exclude utils --select E9,F,I
ruff format scripts --exclude tools --exclude utils --check
```

测试覆盖单位、数据一致性、边界条件与命令行行为；外部程序接口使用替身测试。
