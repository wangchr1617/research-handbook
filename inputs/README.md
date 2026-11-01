# 计算输入模板

输入文件是修改起点，参数应结合体系、目标与软件版本判断。

| 目录 | 内容 |
| --- | --- |
| [vasp](vasp/) | 优化、静态计算、能带等任务的 INCAR 模板 |
| [cp2k](cp2k/) | CP2K 优化、SCF、AIMD 输入 |
| [deepmd](deepmd/) | DeePMD / DP-GEN 配置及 LAMMPS 输入 |
| [nequip](nequip/) | NequIP 配置 |
| [phonopy](phonopy/) | Phonopy 力常数输出配置 |
| [pbs](pbs/) | 按软件命名的 PBS 作业模板 |

使用前按体系修改元素、赝势或基组和计算参数；PBS 模板还需填写工作目录、队列与资源配置。

CP2K 配套实例见 [Fe3GaTe2 计算资料](../examples/cp2k/fe3gate2/)。
