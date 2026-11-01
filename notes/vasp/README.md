# VASP

## 安装与计算准备

| 笔记 | 适用环境 |
| --- | --- |
| [VASP 基础知识](VASP基础知识.md) | 通用；Linux + PBS 运行 |
| [VASP 编译](VASP编译.md) | Linux 集群 |
| [VASPKIT 安装](VASPKIT安装.md) | Windows / macOS / Linux |
| [VASP 并行参数设置](VASP并行参数.md) | Linux 集群；本机小测试 |
| [参数收敛测试](VASP参数收敛测试.md) | 输入与绘图通用；Linux + PBS |
| [参数收敛结果分析（Notebook）](INCAR参数收敛测试.ipynb) | Linux（VASP 计算）；Windows / macOS / Linux（Python 分析） |
| [VASP 批量计算](VASP批量计算.md) | 输入与分析通用；Linux + PBS |
| [训练数据准备](VASP训练数据准备.md) | 数据处理通用；Linux + PBS |
| [机器学习力场](VASP机器学习力场.md) | 支持 MLFF 的 VASP；Linux + PBS |

## 基础计算

| 笔记 | 适用环境 |
| --- | --- |
| [单点能与受力](VASP单点能与受力.md) | 输入与分析通用；Linux + PBS |
| [原子位置优化](VASP原子位置优化.md) | 输入与分析通用；Linux + PBS |
| [晶胞优化](VASP晶胞优化.md) | 输入与分析通用；Linux + PBS |
| [固定晶格优化](VASP固定晶格优化.md) | 专用补丁；Linux + PBS |
| [隐式溶剂计算](VASP隐式溶剂计算.md) | VASPsol；Linux + PBS |
| [第一性原理分子动力学](VASP分子动力学.md) | 输入与分析通用；Linux + PBS |

## 性质计算与分析

| 笔记 | 适用环境 |
| --- | --- |
| [NEB 搜索过渡态](NEB过渡态搜索.md) | Linux 集群（VASP 与 VTST） |
| [能带与态密度入门](VASP能带与态密度.md) | 输入通用；Linux + PBS |
| [态密度计算](VASP态密度计算.md) | 输入与绘图通用；Linux + PBS |
| [能带计算](VASP能带计算.md) | 输入与绘图通用；Linux + PBS |
| [能带反折叠](VASP能带反折叠.md) | Linux + PBS |
| [VASP 弹性常数计算](VASP弹性常数计算.md) | Linux（VASP 与 VASPKIT） |
| [电子结构分析入门](VASP电子结构分析.md) | 分析思路通用 |
| [电子局域函数 ELF](VASP电子局域函数.md) | 输入与分析通用；Linux + PBS |
| [Bader 电荷分析](VASPBader电荷分析.md) | Linux 计算；分析通用 |
| [差分电荷密度](VASP差分电荷密度.md) | Linux 计算；可视化通用 |
| [VASP 拟合 E-V 曲线](VASP能量体积曲线拟合.md) | Linux（VASP 计算与批量脚本） |
| [VASP Lobster 键合分析](LOBSTER键合分析.md) | Linux（VASP 与 LOBSTER） |
| [声子谱计算](VASP声子谱计算.md) | 输入与绘图通用；Linux + PBS |
| [有限差分 Γ 点频率](VASP有限差分振动频率.md) | Linux + PBS |
| [DFPT Γ 点频率](VASP密度泛函微扰振动频率.md) | Linux + PBS |
| [简谐热容](VASP热容计算.md) | 输入与绘图通用；Linux + PBS |
| [静态介电响应](VASP静态介电响应.md) | 输入与分析通用；Linux + PBS |
| [光学性质](VASP光学性质计算.md) | 输入与绘图通用；Linux + PBS |
| [电子输运与电子热导率](VASP电子输运与电子热导率.md) | 输入与绘图通用；Linux + PBS |
| [准谐近似与热膨胀](VASP准谐近似与热膨胀.md) | 输入与绘图通用；Linux + PBS |
| [晶格热导率](VASP晶格热导率计算.md) | 输入与分析通用；Linux + PBS |
| [自旋轨道耦合](VASP自旋轨道耦合.md) | 输入与绘图通用；Linux + PBS |
| [HSE06 杂化泛函](VASP杂化泛函HSE06.md) | 输入与绘图通用；Linux + PBS |
| [DFT+U](VASP的DFT加U计算.md) | 输入与绘图通用；Linux + PBS |
| [选择性原子优化](VASP选择性结构优化.md) | 输入与绘图通用；Linux + PBS |
| [D3(BJ) 色散修正](VASP范德华修正.md) | 输入与绘图通用；Linux + PBS |
| [分子外加电场](VASP外加电场计算.md) | 输入与绘图通用；Linux + PBS |
| [费米面](VASP费米面计算.md) | 输入与绘图通用；Linux + PBS |
| [表面功函数](VASP功函数计算.md) | 输入与绘图通用；Linux + PBS |
| [GW 准粒子能带](VASPGW准粒子能带.md) | 输入与绘图通用；Linux + PBS |
| [BSE 光学响应](VASPBSE光学响应.md) | 输入与绘图通用；Linux + PBS |
| [ACFDT-RPA 关联能](VASPRPA关联能.md) | 输入与绘图通用；Linux + PBS |
| [H 在 Al(111) 上的吸附能](VASP吸附能计算.md) | 输入与绘图通用；Linux + PBS |
| [吸附反应能台阶图](VASP反应能台阶图.md) | 输入与绘图通用；Linux + PBS |
| [表面覆盖度与化学势](VASP表面相图.md) | 输入与绘图通用；Linux + PBS |
| [ZnS 压电张量](VASP压电张量.md) | 输入与绘图通用；Linux + PBS |
| [XAS/XANES 核吸收谱](VASPX射线吸收谱.md) | 输入与绘图通用；Linux + PBS |
| [Dimer 鞍点搜索](VASPDimer鞍点搜索.md) | 输入与绘图通用；Linux + PBS |
| [约束分子动力学](VASP约束分子动力学.md) | 输入与绘图通用；Linux + PBS |
| [Metadynamics 元动力学](VASP元动力学.md) | 输入与绘图通用；Linux + PBS |
| [原子自旋与分子解离能](VASP原子自旋与分子解离能.md) | 输入与绘图通用；Linux + PBS |
| [表面能与薄膜厚度](VASP表面能与薄膜厚度.md) | Linux + PBS；绘图通用 |

## 特色高级计算

| 笔记 | 适用环境 |
| --- | --- |
| [VASP磁各向异性能](VASP磁各向异性能.md) | Linux + PBS；通用分析 |
| [VASPBerry相极化与Born有效电荷](VASPBerry相极化与Born有效电荷.md) | Linux + PBS；通用分析 |
