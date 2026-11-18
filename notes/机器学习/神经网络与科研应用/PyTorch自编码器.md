# PyTorch 自编码器

把一批结构的描述符画到二维图上，首先要决定这张图用来做什么。如果只想看候选覆盖，二维投影能帮助挑出值得回查的区域。如果还要用压缩表示预测性质，就得检查决定性质的结构差异是否被保留。自编码器通过重建输入学习压缩表示，重建损失提供训练信号，后续用途需要另外检验。

## 一、用已知低维的数据检验重建

在已安装 PyTorch 的环境中把下面的代码保存为 `autoencoder_demo.py`，执行 `python autoencoder_demo.py`。示例使用 CPU 并在脚本内造数据。

```python
import torch
from torch import nn

torch.manual_seed(7)
torch.set_num_threads(1)
latent = torch.randn(128, 2)
projection = torch.randn(2, 6)
x = latent @ projection
encoder = nn.Sequential(nn.Linear(6, 12), nn.ReLU(), nn.Linear(12, 2))
decoder = nn.Sequential(nn.Linear(2, 12), nn.ReLU(), nn.Linear(12, 6))
model = nn.Sequential(encoder, decoder)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
loss_fn = nn.MSELoss()
with torch.no_grad():
    initial = loss_fn(model(x), x).item()
for step in range(300):
    optimizer.zero_grad(set_to_none=True)
    loss = loss_fn(model(x), x)
    loss.backward()
    optimizer.step()
model.eval()
with torch.inference_mode():
    code = encoder(x)
    final = loss_fn(model(x), x).item()
print("latent shape =", tuple(code.shape))
print("reconstruction MSE:", initial, "->", final)
assert code.shape == (128, 2)
assert final < initial
```

这里用一个 `[128, 2]` 的矩阵乘上 `[2, 6]` 的投影矩阵，生成 128 个六维样本。编码器将每行压成两个数，解码器再还原为六维。代码检查潜在变量形状和训练前后的重建误差。由于六维数据来自线性映射，中心化后的矩阵秩最多为 2，同样宽度的 PCA 在数值精度内就能重建。即使自编码器得到很小的误差，学到的两个坐标也未必逐列对应造数据时的两个变量。

## 二、拿结构差异来检验压缩后的表示

手册的[原子描述符案例](../../../examples/machine-learning/atomistic-models/README.md)用两个键长相同、夹角不同的 OHH 构型检查 SOAP 表示。对更丰富的一批结构拟合压缩模型后，可以把这对构型作为检查点，看看夹角差异在压缩后是否依然可辨。如果目标是预测某项性质，还应在同一留出划分中比较原始描述符、[PCA](../传统模型/降维.md)与自编码器的下游误差。两个构型只能用来检查一种几何差别，训练和评估仍需要覆盖目标体系的样本。

示例的 MSE 对所有输入分量一起计分。描述符尺度差异大时，先用训练集拟合标准化参数，再将同一变换应用于验证集和测试集。除了总误差，也可以检查课题关心的分量或结构组，看看平均误差有没有掩盖局部失真。来自同一轨迹的相邻帧宜留在同一组，避免用训练样本的近邻检验压缩效果。

如果目的是生成新结构，还需要另外定义潜在变量的取样方式，并检验解码所得的对象能否满足组成与几何约束。这个示例的解码器只输出六维向量，训练过程中也没有拟合可供采样的概率分布。

实现沿用 [PyTorch 模型与优化流程](https://docs.pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html)，本篇数据与网络为教学示例。
