# CP2K 最小计算案例

在各目录查看输入、PBS 作业脚本和结果检查方法。基组与势文件由集群 CP2K 安装提供。

| 案例 | 内容 |
| --- | --- |
| [用 Multiwfn 生成输入](multiwfn-input/) | [笔记](../../../notes/CP2K/基础与准备/用Multiwfn生成CP2K输入文件.md) |
| [水分子单点能与受力](single-point/) | [笔记](../../../notes/CP2K/结构优化/CP2K单点能与受力.md) |
| [周期水二聚体 CDA](periodic-cda/README.md) | [完整轨道、周期重叠与片段分解](../../../notes/CP2K/电子结构与响应/CP2K与Multiwfn的周期CDA分析.md) |
| [周期水二聚体响应与局部场](periodic-response/README.md) | TDA、NTO、NCI/IGMH、赝势元数据与周期平移 |
| [水分子几何优化](geometry-optimization/) | [笔记](../../../notes/CP2K/结构优化/CP2K几何优化.md) |
| [硅晶胞优化](cell-optimization/) | [笔记](../../../notes/CP2K/结构优化/CP2K晶胞优化.md) |
| [水分子短程 NVT](molecular-dynamics/) | [笔记](../../../notes/CP2K/动力学与反应/CP2K分子动力学.md) |
| [水分子振动频率](vibrational-analysis/) | [笔记](../../../notes/CP2K/动力学与反应/CP2K振动频率.md) |
| [CI-NEB 受约束迁移](neb/) | [参数与操作](../../../notes/CP2K/动力学与反应/CP2K过渡态搜索.md) |
| [批量单点与标签导出](batch-single-points/) | [批量计算](../../../notes/CP2K/批量计算与训练数据/CP2K批量计算.md)与[训练数据](../../../notes/CP2K/批量计算与训练数据/CP2K训练数据准备.md) |
| [PBE0 杂化泛函](hybrid-pbe0/) | [参数与操作](../../../notes/CP2K/电子结构与响应/CP2K杂化泛函PBE0.md) |
| [选择性原子优化](selective-optimization/) | [参数与操作](../../../notes/CP2K/结构优化/CP2K选择性结构优化.md) |
| [D3(BJ) 色散修正](dispersion-d3/) | [参数与操作](../../../notes/CP2K/电子结构与响应/CP2K范德华修正.md) |
| [静电场响应](electric-field/) | [参数与操作](../../../notes/CP2K/电子结构与响应/CP2K静电场响应.md) |
| [约束分子动力学](constrained-md/) | [参数与操作](../../../notes/CP2K/动力学与反应/CP2K约束分子动力学.md) |
| [Metadynamics 元动力学](metadynamics/) | [参数与操作](../../../notes/CP2K/动力学与反应/CP2K元动力学.md) |
| [TDDFPT 电子激发态](tddfpt/) | [参数与操作](../../../notes/CP2K/电子结构与响应/CP2K电子激发态.md) |
| [CP2K GAPW 全电子计算](gapw-all-electron/) | [方法与检查](../../../notes/CP2K/电子结构与响应/CP2KGAPW全电子计算.md) |
| [CP2K 的 ADMM 杂化泛函](admm-hybrid/) | [方法与检查](../../../notes/CP2K/电子结构与响应/CP2K的ADMM杂化泛函.md) |

[晶胞、振动与路径接口案例](structure-modes-path/README.md)对照不同晶胞记法与扩胞表示，并提供实际水振型读取和显式 NEB 初始插点。
