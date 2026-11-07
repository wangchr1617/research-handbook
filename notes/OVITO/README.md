# OVITO

按学习顺序阅读：[阅读目录](阅读目录.md)。

先在图形界面核对一个小结构，再固定分析参数，用 Python 对轨迹或多个文件重复处理。

| 顺序 | 笔记 | 适用环境与内容 |
| --- | --- | --- |
| 1 | [安装与基础操作](OVITO安装与基础操作.md) | Windows / macOS / Linux 桌面；下载、晶胞、类型与管线 |
| 2 | [配位数与径向分布函数](配位数与径向分布函数.md) | 图形界面 / Python；cutoff、RDF 与周期边界 |
| 3 | [OVITO Python 批量分析](OVITOPython批量分析.md) | 本机小例子 / Linux 集群；逐帧统计与导出 |
| 4 | [Wigner-Seitz 缺陷分析](Wigner-Seitz缺陷分析.md) | OVITO Python；参考格点、空位与过量原子 |
| 5 | [Docker 与 Apptainer 环境](OVITO容器环境配置.md) | Linux；系统依赖受限时的部署补充 |

每次分析保留输入来源、长度单位、周期边界和修改器顺序。粒子类型名称、颜色与渲染参数只是显示设置，不能代替数值分析与物理判断。
