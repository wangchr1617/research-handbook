# MMonCa 安装与事件参数核对

MMonCa 通过 Tcl 输入脚本组织初始化、事件表、温度程序和输出。首次运行建议先用上游自带的测试或示例，确认可执行文件、材料配置与输入语法相互匹配，再替换成目标材料的参数。

## 一、先让二进制和材料表配套

1. 从[上游项目](https://raw.githubusercontent.com/MMonCa/MMonCa/master/README)获取源码并记录提交号。在源码根目录执行 `make help` 查看平台目标，检查对应的 `sysmakes/Makefile.*` 中的编译器与 Tcl 路径，再执行 `make <平台目标>`。上游构建脚本会把编译好的程序放在 `Obj_<平台目标>/mmonca`（尖括号内为待替换的平台目标名）。随后用与可执行文件同一版本的 `config` 目录设置 `MCPATH`，在独立目录中运行上游随附示例。将配置路径和案例名代入[运行命令](MMonCa点缺陷退火与扩散.md#一先重现-α-fe-的等时退火输入)，确认配置已被正确读入且第一段退火能顺利完成。
2. 阅读输入脚本时，注意区分 Tcl 变量和 MMonCa 命令，并依次核对材料表、晶胞与边界、初始缺陷或级联导入、热处理以及数据导出等环节，同时检查输出的初始粒子数、几何边界和实际温度。

## 二、逐项核对事件速率与停止条件

1. 将迁移、捕获、解离和复合分开建表。若采用 Arrhenius 速率 $r=\nu\exp[-E_a/(k_BT)]$，每项都要写明势垒、前因子及单位。若参数来自扩散系数，需先检查配置项是否直接接收扩散前因子；需要换算为跃迁速率时，则按跳距、空间维度和方向数处理，尤其要区分单通道频率与总逃逸频率，详见[从迁移势垒到材料中的扩散](../VASP/表面与反应/NEB过渡态搜索.md#五从迁移势垒到材料中的扩散)。
2. 按上游定义，`anneal temp=...` 接收的温度单位为摄氏度，而在计算 Arrhenius 指数时程序内部使用的是开尔文。停止条件可以设为时间、事件数或界面深度，比较不同样本时应记录实际触发的是哪一项。

先试一个只有一种缺陷的均匀体相，检查无反应时粒子数守恒与扩散趋势。再加复合、成簇及边界捕获，核对元素和缺陷计数。参考 [MMonCa 构建脚本](https://raw.githubusercontent.com/MMonCa/MMonCa/master/Makefile)、[MMonCa 手册](https://github.com/MMonCa/MMonCa/blob/master/doc/MMonCa.tex)与 [anneal 定义](https://github.com/MMonCa/MMonCa/blob/master/doc/commands/anneal.tex)。
