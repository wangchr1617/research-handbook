# PyTorch 循环神经网络

**适用环境：已安装 PyTorch 的 Python 环境，下面在 CPU 演示 GRU。**

RNN 按时间步更新隐藏状态，GRU 和 LSTM 用门控机制处理较长的依赖。以一段时间序列预测一个标量为例，输入包含 batch、时间和特征三个维度。

## GRU 的输入与输出

保存为 `gru_demo.py`，执行 `python gru_demo.py`：

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

`batch_first=True` 对应输入 `[4,20,3]`：四条序列，每条 20 个时间步，每步三个特征。最后一层隐藏状态 `hidden[-1]` 用来做整条序列的回归；逐时间步预测则使用 `output`。

## 时间序列如何划分

以轨迹预测为例，按时间或独立轨迹划分训练、验证、测试，避免重叠窗口跨越集合边界。输入窗口只能包含预测时已经知道的信息，不能把未来值放进归一化或特征中。

变长序列需要用真实长度、打包序列或掩码处理补齐位置，不能默认最后一个补零时间步代表真实结束。长序列是否用循环网络、卷积或 Transformer，应根据数据规模、任务和基线结果比较。

参考：[PyTorch GRU](https://docs.pytorch.org/docs/stable/generated/torch.nn.GRU.html)。
