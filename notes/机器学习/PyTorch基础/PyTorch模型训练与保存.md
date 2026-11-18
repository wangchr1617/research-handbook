# PyTorch 模型训练与保存

**适用环境：Windows / macOS / Linux，已安装 PyTorch；下面的小数据在 CPU 训练，无需下载数据集。**

重新加载权重后，如果准确率和最后一轮不同，先问保存的是哪一轮。这里按验证损失保留最佳权重。比较时需要对照同一轮、同一批输入的输出。

以一个二维二分类问题为例，先把数据、网络、损失、优化和保存完整串起来。它用于理解训练流程，不代表真实课题的数据难度。

## 一、先把首个 batch 对到模型和损失

把本篇三个 Python 代码块依次保存到同一个 `train_demo.py`：

```python
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

torch.manual_seed(7)
torch.set_num_threads(1)
x = torch.randn(512, 2)
y = (x[:, 0] + x[:, 1] > 0).long()
train_x, valid_x = x[:384], x[384:]
train_y, valid_y = y[:384], y[384:]
loader = DataLoader(TensorDataset(train_x, train_y), batch_size=32, shuffle=True)

model = nn.Sequential(nn.Linear(2, 16), nn.ReLU(), nn.Linear(16, 2))
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
```

`Linear(2,16)` 把两个特征映射到 16 个隐藏单元；最终输出两个类别的 logits。`CrossEntropyLoss` 直接接收 logits 和整数标签，不先手动加 Softmax。`DataLoader` 负责分 batch，`shuffle=True` 用于打乱训练数据。

## 二、先验证一次更新，再比较各轮

```python
best_loss = float("inf")
for epoch in range(30):
    model.train()
    for features, labels in loader:
        optimizer.zero_grad(set_to_none=True)
        loss = loss_fn(model(features), labels)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.inference_mode():
        logits = model(valid_x)
        valid_loss = loss_fn(logits, valid_y).item()
        accuracy = (logits.argmax(dim=1) == valid_y).float().mean().item()
    if valid_loss < best_loss:
        best_loss = valid_loss
        torch.save(model.state_dict(), "best-model.pt")
    if (epoch + 1) % 10 == 0:
        print(epoch + 1, "valid loss =", valid_loss, "accuracy =", accuracy)
```

排错时可先只跑一个 batch。输入应是 `[32,2]`，模型输出 `[32,2]`，整数标签为 `[32]`，因为这里传的是类别索引。调用 `backward()` 后查看参与训练的参数是否有有限梯度，再确认 `step()` 更新了权重。单步异常时回到张量形状和梯度链排查。 [自动微分](PyTorch自动微分.md)

执行 `python train_demo.py`。应看到验证损失下降、准确率明显高于随机猜测，当前目录产生 `best-model.pt`。这是人工数据的流程检查；正式研究还需要独立测试集，不能用测试集反复选择模型。

材料构型常相互关联，应按材料、轨迹或构型来源划分数据；同一轨迹的近邻帧随机混入训练与测试可能高估泛化能力。标准化参数只从训练集拟合。

## 三、重新加载，核对保存时的预测

```python
restored = nn.Sequential(nn.Linear(2, 16), nn.ReLU(), nn.Linear(16, 2))
restored.load_state_dict(torch.load("best-model.pt", map_location="cpu", weights_only=True))
restored.eval()
with torch.inference_mode():
    prediction = restored(valid_x).argmax(dim=1)
print("restored accuracy =", (prediction == valid_y).float().mean().item())
```

要核对保存与加载，可在保存最佳权重的分支里另存当时验证输入的少量 logits，再与重载后的输出在相同模式和精度下逐项比较。准确率相同只表示类别判定一致。

加载时网络结构要一致，并记录网络参数、预处理、标签和包版本，才能对应到保存的 `state_dict`。

若要断点续训，还应保存优化器、轮次及随机状态；单有权重只能恢复模型参数，不能精确恢复整个训练过程。

只加载来源可信的模型文件。要用 GPU 时，将模型、特征和标签移到同一设备，先在小数据上核对结果。

参考：[DataLoader](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html)、[优化循环](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)、[模型保存与加载](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)。
