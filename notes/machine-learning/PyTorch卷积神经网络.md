# PyTorch 卷积神经网络

**适用环境：已安装 PyTorch 的 Python 环境，下面在 CPU 检查网络维度。**

卷积层通过局部卷积核提取特征，并在不同空间位置共享权重。二维图像输入通常写成 `[batch, channel, height, width]`，先把这四个维度弄清楚，再增加网络深度。

## 一个小型图像分类网络

保存为 `cnn_demo.py`，执行 `python cnn_demo.py`：

```python
import torch
from torch import nn

torch.manual_seed(7)
model = nn.Sequential(
    nn.Conv2d(1, 8, kernel_size=3, padding=1),
    nn.ReLU(),
    nn.MaxPool2d(2),
    nn.Conv2d(8, 16, kernel_size=3, padding=1),
    nn.ReLU(),
    nn.AdaptiveAvgPool2d((1, 1)),
    nn.Flatten(),
    nn.Linear(16, 10),
)
images = torch.randn(4, 1, 28, 28)
labels = torch.tensor([0, 1, 2, 3], dtype=torch.long)
logits = model(images)
loss = nn.CrossEntropyLoss()(logits, labels)
loss.backward()
print("output shape =", tuple(logits.shape))
print("loss =", loss.item())
assert logits.shape == (4, 10)
assert torch.isfinite(loss)
assert model[0].weight.grad is not None
```

输入是四张单通道、28 × 28 的演示图像；输出是每张图的十个类别分数。`padding=1` 让这个 3 × 3 卷积保持空间尺寸，池化再缩小尺寸，全局平均池化得到固定长度特征。

这个例子只检查前向与反向传播，随机输入没有分类意义。真实训练时替换为自己的 Dataset，并沿用 [训练与保存](PyTorch模型训练与保存.md)的循环。

## 使用时看什么

图像的灰度范围、通道顺序与归一化方式应保持一致。迁移学习时采用预训练权重对应的预处理，不只加载一个网络名称。

二维卷积适合图像或规则网格数据。原子坐标是非规则点集，不能仅把坐标排成矩阵就认为获得了平移、旋转和置换不变性；材料势函数通常需要相应的图表示或等变网络。

参考：[PyTorch Conv2d](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv2d.html)。
