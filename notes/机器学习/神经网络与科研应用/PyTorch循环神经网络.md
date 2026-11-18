# PyTorch 循环神经网络

拿一段分子动力学轨迹预测下一帧的标量时，最简单的基线是直接沿用最后一帧的值。若最近几帧的变化方向还能提供信息，可以用一个有限的历史窗口做预测。GRU 逐步读取窗口内的特征，通过门控更新隐藏状态，让回归头使用整段历史的信息。能否胜过只用最近一帧的基线，要在独立数据上比较。

## 一、二十帧为什么只输出一个值

在已安装 PyTorch 的环境里把示例保存为 `gru_demo.py`，执行 `python gru_demo.py`。CPU 上生成的随机输入和随机标签用于检查维度与反向传播。

```python
import torch
from torch import nn

torch.manual_seed(7)
gru = nn.GRU(input_size=3, hidden_size=16, batch_first=True)
head = nn.Linear(16, 1)
sequence = torch.randn(4, 20, 3)
target = torch.randn(4, 1)
output, hidden = gru(sequence)
prediction = head(hidden[-1])
loss = nn.MSELoss()(prediction, target)
loss.backward()
print("all time steps =", tuple(output.shape))
print("hidden state =", tuple(hidden.shape))
print("prediction =", tuple(prediction.shape))
assert output.shape == (4, 20, 16)
assert hidden.shape == (1, 4, 16)
assert prediction.shape == target.shape
```

`batch_first=True` 让输入按 `[4, 20, 3]` 排列，即四个窗口、每个窗口二十帧、每帧三个特征。`output` 保留每个时间步的 16 维表示，形状为 `[4, 20, 16]`。`hidden` 的第一维在本例中对应层数，形状是 `[1, 4, 16]`。取 `hidden[-1]` 后，每个窗口剩一个 16 维向量，回归头再把它变成一个标量，和 `[4, 1]` 的标签逐项比较。若任务需要逐帧输出，则把回归头接在 `output` 上，并按目标时间对齐逐帧标签。

窗口长度不同时，直接在尾部补零会让 GRU 继续更新状态。此时 `hidden[-1]` 可能已经包含补齐部分的影响。可以按真实长度打包输入，或在这个单向网络的输出中取每条序列最后一个有效时间步。只掩盖损失里的补齐位置，无法修正已经读过补零的隐藏状态。参见 [PyTorch GRU 文档](https://docs.pytorch.org/docs/stable/generated/torch.nn.GRU.html)。

## 二、先切轨迹，再构造重叠窗口

例如用第 1 到 20 帧预测第 21 帧，下一窗口用第 2 到 21 帧预测第 22 帧。把这两个窗口随机分到训练集和验证集，会共享十九帧输入，前一个窗口的标签还出现在后一个窗口的输入中。评估独立轨迹上的表现时，先按轨迹划分再切窗口。只有一条轨迹时，可以按时间切连续区段，在各段内独立构造输入和标签，避免窗口跨过分界。标准化统计量也只从训练段拟合。参见[数据划分与模型评估](../基础与评估/数据划分与模型评估.md)。

在相同的预测步长、划分和误差单位下比较基线与 GRU。逐步改变窗口长度，看增加历史后误差是否降低。这样才能判断时序模型的收益是否足以支撑它比简单基线多出的训练开销。
