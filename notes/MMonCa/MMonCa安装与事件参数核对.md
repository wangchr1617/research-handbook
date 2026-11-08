# MMonCa 安装与事件参数核对

MMonCa 用 Tcl 输入组织初始化、事件表、温度程序和输出。首次运行先用上游自带的测试或示例确认二进制、材料配置与输入语法匹配，再替换成目标材料的参数。

1. 从[上游项目](https://raw.githubusercontent.com/MMonCa/MMonCa/master/README)取源码，记录提交号。在源码根目录执行 `make help` 查看平台目标，检查对应的 `sysmakes/Makefile.*` 中编译器和 Tcl 路径，再执行 `make <平台目标>`。上游构建脚本把程序放在 `Obj_<平台目标>/mmonca`，其中尖括号内是待替换的名称。用与可执行文件同一版本的 `config` 设置 `MCPATH`，先在独立目录运行上游随附示例。将配置路径和案例名代入[运行命令](MMonCa点缺陷退火与扩散.md#从上游案例开始)，确认配置被读入且第一段退火能完成。
2. 读输入时分清 Tcl 变量和 MMonCa 命令。依次确认材料表、晶胞与边界、插入缺陷或级联、热处理以及数据导出。检查输出的初始粒子数、几何边界和实际温度。
3. 将迁移、捕获、解离和复合分开建表。若用 Arrhenius 率 $r=\nu\exp[-E_a/(k_BT)]$，每项都写明势垒、前因子及单位。模型若输入扩散前因子，按跳距、方向数与事件约定换算，勿直接填成尝试频率。
4. 输入 `anneal temp=...` 时按上游定义用摄氏度，计算 Arrhenius 指数的温度是开尔文。停止条件可用时间、事件数或界面深度，比较样本时记录实际触发的是哪一项。

先试一个只有一种缺陷的均匀体相，检查无反应时粒子数守恒与扩散趋势。再加复合、成簇及边界捕获，核对元素和缺陷计数。参考 [MMonCa 构建脚本](https://raw.githubusercontent.com/MMonCa/MMonCa/master/Makefile)、[MMonCa 手册](https://github.com/MMonCa/MMonCa/blob/master/doc/MMonCa.tex)与 [anneal 定义](https://github.com/MMonCa/MMonCa/blob/master/doc/commands/anneal.tex)。
