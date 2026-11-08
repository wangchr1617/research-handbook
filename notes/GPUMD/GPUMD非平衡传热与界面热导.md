# GPUMD 非平衡传热与界面热导

在盒子中设置热源与冷源，维持稳态热流。均匀区域用温度梯度求热导率，跨界面则用两侧外推的温度跃变求热边界电导。与[均匀驱动 HNEMD](GPUMD热导率与谱热流.md)对照时，应统一势、温度和几何归一化。

## 从分组到温度剖面

在 `model.xyz` 中用第 0 套分组定义热源、热汇和其余层，先检查每组原子数、空间位置和边界连通。一个输入片段如下，组号必须与模型对应。

```text
ensemble heat_lan 300 100 10 0 1
compute 0 100 10 temperature
```

热源和热汇目标温度是 310 K 与 290 K。10 K 是相对中心温度的偏移。`compute` 每 100 步采样并对 10 个样本平均后写出一行。完整输入还需势、初态、步长与 `run`，应先等温平衡再打开驱动。

## 求热流与检验线性

`compute.out` 的最后两列为热源和热汇的累计交换能量（eV）。从其稳态斜率提取 $\dot Q$，比较热源与热汇的能量收支。按横截面积和并行传热路径数量分配热流。对周期对称的双路径，每条路径的通量为 $|\dot Q|/(2A)$。非对称路径需分别确定热流。

在远离热浴与界面强分层区的均匀区域拟合温度。热导率用 $|j/\nabla T|$，热边界电导用 $j/\Delta T_{\rm int}$。至少改变驱动温差和长度，检查稳态、线性响应与尺寸依赖。用 `compute_shc` 做谱分析时，先对齐分组、频率单位和积分归一化，再对照总热流。

参考 [GPUMD 热输运系综](https://gpumd.org/gpumd/input_parameters/ensemble_heat.html)、[分组平均输出](https://gpumd.org/gpumd/output_files/compute_out.html)及[热输运理论](https://gpumd.org/theory/heat_transport.html)。
