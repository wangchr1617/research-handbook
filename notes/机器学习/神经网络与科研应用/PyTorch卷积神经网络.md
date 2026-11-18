# PyTorch 卷积神经网络

假设手头有一批显微图，想根据颗粒、孔洞或纹理给每张图分类。同一类局部特征可能出现在图像的不同位置，卷积层可以用同一组权重在各处寻找它。一旦换成按空间坐标排列的网格之外的数据，就要重新检查卷积核看到的“邻居”是否有实际含义。

## 一、先用一批图确认网络看到的是什么

在已安装 PyTorch 的环境中把下面的代码保存为 `cnn_demo.py`，执行 `python cnn_demo.py`。示例用 CPU 和随机张量检查维度及反向传播。

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

四张灰度图组成形状为 `[4, 1, 28, 28]` 的批次，第二维是通道数。第一层的 3 × 3 卷积用 `padding=1` 保持宽高，通道增至 8。最大池化后变成 `[4, 8, 14, 14]`，第二个卷积把通道增至 16。全局平均池化将每张特征图压成一个数，展平后每张输入图对应 16 个特征，最后输出 `[4, 10]` 的分类 logits。四个标签分别给出四张图的类别编号，形状是 `[4]`。

如果 Dataset 读出单张图的形状是 `[28, 28]`，组批后要补出灰度通道。彩色数据若由图像库读成通道在末尾的数组，应先把轴调到正确位置，再看通道数是否与第一层一致。先检查一批真实数据及标签，再接上[训练与保存](../PyTorch基础/PyTorch模型训练与保存.md)里的循环。演示中的有限损失和梯度只说明计算路径可用。

## 二、显微图切成小块后，验证集该怎么留

同一张原图切出的图块往往共享背景和成像条件。若随机打散图块再划分，训练集和验证集可能各拿到同一颗粒附近的相邻区域，验证分数就难以反映新样品上的表现。按原始图像或样品 ID 划分，并检查标签在各组的覆盖；如果要检验跨采集批次的表现，就留出整批图像。使用预训练权重时核对通道顺序、灰度范围和对应预处理。参见[数据划分与模型评估](../基础与评估/数据划分与模型评估.md)。

全局平均池化保留各通道的整体响应，适合示例的整图分类。若任务是找出裂纹在图上的位置，就需要保留空间输出，另设定位或分割的标签与评价方式。原子构型也有自己的邻域关系，直接把坐标表的相邻行交给二维卷积，并不会自然得到符合原子对称性的表示。可沿[手册中的原子描述符和建模案例](../../../examples/machine-learning/atomistic-models/README.md)对照两类输入。

参考 [PyTorch Conv2d](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv2d.html)。
