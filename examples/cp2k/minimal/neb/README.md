# CP2K 受约束硅原子迁移

7 原子硅周期小胞中，六个背景原子固定，一个原子在两个局部能谷之间迁移。适合学习端点优化、路径插值和 CI-NEB，不作为稀释缺陷势垒的定量模型。

[笔记](../../../../notes/cp2k/CP2K过渡态搜索.md)给出输入解释和 PBS 操作。准备 CP2K、MPI 和 `requirements.txt` 中的 Python 依赖，确认可找到安装数据目录中的基组与势后，执行 `qsub job.pbs`。

`run.py` 默认执行完整流程；可用 `--stage endpoints` 先优化端点，确认后在同一目录以 `--stage neb` 继续。分阶段运行时应保持结构和电子设置一致。已有完整结果时只运行 `python3 postprocess.py` 即可重画 `si-neb-cp2k.png`，不必重算端点与路径。
