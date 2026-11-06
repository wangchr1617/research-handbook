# PyTorch 自编码器

**适用环境：已安装 PyTorch 的 Python 环境；CPU 小例子，无需外部数据。**

自编码器用编码器把输入映射到潜在变量，再由解码器重建输入。它可用于学习压缩表示，但重建误差小不代表潜在空间一定保留了课题关心的物理信息。

## 跑通重建训练

保存为 `autoencoder_demo.py`，执行 `python autoencoder_demo.py`：

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

这里的六维数据由二维变量生成，方便理解压缩。代码在同一小批数据上训练与检查，只能说明网络学会了这批数据的重建；正式评估需要未参与训练的验证和测试数据。

## 用于科研数据

不同描述符的尺度会影响均方误差，先在训练集上拟合标准化参数。潜在变量维度通过验证集比较，也可以和 [PCA 等降维方法](../传统模型/降维.md)对照。

普通自编码器不是概率生成模型。想从潜在空间随机采样生成新结构，还需要考虑采样分布、结构约束和生成质量，不能把任意潜在点解码后直接当作合理结构。

实现沿用 [PyTorch 模型与优化流程](https://docs.pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html)，本篇数据与网络为说明用示例。
