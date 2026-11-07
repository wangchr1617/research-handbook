# GPUMD / NEP

`check_gpumd.py` 输出任务状态和完整轨迹帧数。结构优化统一使用 [calorine_relax.py](calorine/calorine_relax.py)，通过 `--mode ions|cell|constant-volume` 选择模式，`--backend calorine|pynep` 选择计算器。

## 文件

- [calorine/](calorine/)
- [check_gpumd.py](check_gpumd.py)：检查 GPUMD 子任务输出。
- [run_gpumd_workflow.py](run_gpumd_workflow.py)：GPUMD 分子动力学与主动学习流程草稿，使用前检查入口与采样参数；预测分支尚未实现。
- [evaluate_nep.py](evaluate_nep.py)：用 NEP 计算能量，与 [analyze_energy_data.py](../analysis/analyze_energy_data.py) 配合使用。
- [combine_nep_loss.py](combine_nep_loss.py)：合并两个损失数据文件，并进行时间轴的平移。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
