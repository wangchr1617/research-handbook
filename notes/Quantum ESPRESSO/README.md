# Quantum ESPRESSO

按学习顺序阅读：[阅读目录](阅读目录.md)。

先用[硅原胞 SCF](QE基础知识.md)验收 `pw.x`，再从同一基态数据分出[能带和态密度](QE能带与态密度.md)。如果关心优化后的晶格，先读 [GeTe 结构优化](QE结构优化.md)；判断振动稳定性可沿[硅声子流程](QE声子谱计算.md)逐步核对动力学矩阵和色散。

## 笔记导航

| 笔记 | 适用环境 |
| --- | --- |
| [QE 基础知识](QE基础知识.md) | 通用；Linux + PBS 运行 |
| [QE 编译](QE编译.md) | Linux 集群 |
| [QE 声子谱计算](QE声子谱计算.md) | Linux（Quantum ESPRESSO） |
| [QE 结构优化](QE结构优化.md) | Linux（Quantum ESPRESSO） |
| [Quantum ESPRESSO 能带与态密度](QE能带与态密度.md) | Si 能带、均匀网格 DOS 与后处理 |
