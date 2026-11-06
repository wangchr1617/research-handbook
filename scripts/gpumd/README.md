# GPUMD / NEP

`check_gpumd.py` 输出任务状态和完整轨迹帧数。结构优化统一使用 [calorine_relax.py](calorine/calorine_relax.py)，通过 `--mode ions|cell|constant-volume` 选择模式，`--backend calorine|pynep` 选择计算器。

## 文件

- [calorine/](calorine/)
- [check_gpumd.py](check_gpumd.py)：检查 GPUMD 子任务输出。
- [gpumd_tool.py](gpumd_tool.py)：使用GPUMD进行分子动力学模拟、主动学习和预测。
- [nep_evaluate.py](nep_evaluate.py)：使用NEP计算器计算给定模型的能量，并将结果保存到文件中。结合脚本analyze_energy_data.py使用。
- [nep_loss_combine.py](nep_loss_combine.py)：合并两个损失数据文件，并进行时间轴的平移。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
