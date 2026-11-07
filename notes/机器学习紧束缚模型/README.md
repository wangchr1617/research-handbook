# 机器学习紧束缚模型

按学习顺序阅读：[阅读目录](阅读目录.md)。

**适用环境：通用（原理）；数值例子使用 CPU 与 NumPy。**

本专题沿“选轨道 → 定义在位与跃迁 → 组装电子模型 → 学习参数或修正 → 检查电子性质”展开。先学会手算双原子和一维链，再理解机器学习改变了哪一部分。

## 目录与学习路线

| 目录 | 内容 |
| --- | --- |
| [基础与比较](基础与比较/README.md) | 双原子能级、一维链、非正交基、SK 方向依赖和数据比较 |
| [环境依赖 SK](环境依赖SK/README.md) | DeePTB-SK：从固定两中心积分走向环境相关参数 |
| [可微 DFTB](可微DFTB/README.md) | DFTBML 与 TBMaLT：把近似电子计算纳入训练链 |
| [Wannier 与谱学习](Wannier与谱学习/README.md) | 局域子空间、规范对齐、TBworks 与能谱监督 |

建议从[从双原子到紧束缚能带](基础与比较/从双原子到紧束缚能带.md)开始。更一般的轨道矩阵、等变性与 SOC 见[机器学习哈密顿量](../机器学习哈密顿量/README.md)。

## 演进与团队脉络

1954 年 Slater–Koster 系统整理局域轨道跃迁的方向结构；1990 年代的 DFTB / SCC-DFTB 从 DFT 近似组织有效模型；Wannier 局域化及 Wannier90 提供从第一性原理结果构造子空间模型的工具。2018 年的可微 DFTB 层、2021–2022 年的 TBworks、2023 年的 DFTBML / TBMaLT 和 2023–2024 年的 DeePTB 工作，把参数学习与构型相关电子采样进一步结合。作者、合作单位和预印本/期刊年份见专篇。

这些方法从不同层面组织电子模型：SK 规定矩阵形式，DFTB 保留近似电子能量与自洽过程，Wannier 规定局域表示，机器学习可在其上调整参数或预测矩阵。

## 横向比较

| 方法 | 学习与输出 | 何时优先阅读 |
| --- | --- | --- |
| [DeePTB-SK](环境依赖SK/DeePTB-SK.md) | 环境相关 SK 参数，常用能谱监督 | 想从结构快速得到有效能带模型 |
| [DFTBML](可微DFTB/DFTB与DFTBML.md) | 可解释径向函数与半经验模型参数 | 想用性质数据改进量子化学近似 |
| [TBMaLT](可微DFTB/TBMaLT.md) | 可微 TB 框架，具体学习对象由方案决定 | 想开发或比较电子模型修正 |
| [Wannier 表示](Wannier与谱学习/Wannier表示与规范对齐.md) | 生成、对齐和学习局域子空间矩阵 | 已有第一性原理矩阵与轨道投影 |
| [TBworks](Wannier与谱学习/TBworks与能谱监督.md) | 轨迹构型到有效矩阵，以能谱训练 | 想理解电子性质与 MD 采样结合 |

比较前固定轨道数、能窗、参考理论和目标物性。谱一致不代表矩阵或波函数唯一，完整要求见[数据与横向比较](基础与比较/数据与横向比较.md)。

## 与原子动力学如何连接

```mermaid
flowchart LR
    accTitle: 原子采样与电子模型协作
    accDescr: 势函数提供核构型，电子模型在其上预测矩阵与性质，电子和核两个模型需分别验证。
    potential_model["势函数与原子采样"] --> structures["目标条件下的构型"]
    structures --> electronic_model["ML-TB 预测参数或矩阵"]
    electronic_model --> electronic_solver["电子求解与算符"]
    electronic_solver --> observable["能谱、响应或输运"]
```

由[势函数](../机器学习势函数/README.md)生成轨迹、由电子代理采样性质，是一种常见组合；二者的数据域和参考条件必须相容。TB 模型若没有完整总能表达及导数，不能直接作为 MD 力场。

配套实践见[代码案例](../../examples/machine-learning/atomistic-models/README.md)和[完整模型输入](../../inputs/machine-learning/README.md)。

资料检索截至 2026-11-06。各方法的元素、参数文件和软件接口随版本核对。
