# PyTorch 自动微分

**适用环境：已安装 PyTorch 的 Python 环境；本例在 CPU 运行。**

训练时遇到 `.grad` 为空、梯度逐批变大，先用一个可手算的导数确认计算图和累加行为。研究原子势时，再用同样的办法检查能量到坐标、力到参数两段求导链。

自动微分利用运算链式法则计算导数。PyTorch 在前向计算时记录需要求导的操作，调用 `backward()` 后把梯度累加到叶子张量的 `.grad` 中。

## 一、先算一个能手工核对的导数

保存为 `autograd_demo.py`，执行 `python autograd_demo.py`：

```python
import torch

x = torch.tensor(2.0, requires_grad=True)
y = x**3 + 2*x

y.backward()
print("y =", y.item())
print("dy/dx =", x.grad.item())
assert y.item() == 12.0
assert x.grad.item() == 14.0
```

因为导数为 $3x^2+2$，在 $x=2$ 时得到 `14`。`requires_grad=True` 表示需要记录它的梯度，`backward()` 默认针对标量结果求导。

## 二、用第二次反向传播检查累加

接着第一段代码，在不清空 `x.grad` 的情况下重新执行 `(x**3 + 2*x).backward()`，预期得到 28。然后设置 `x.grad = None`，重新计算表达式并反向传播，预期回到 14。每次都重建表达式，以便把测试限定在梯度累加。

每次反向传播会累加梯度。训练时通常每个 batch 先执行 `optimizer.zero_grad(set_to_none=True)`，再前向计算、反向传播和更新。只有明确进行梯度累积时，才有意跨 batch 保留梯度。

推理时可用 `torch.inference_mode()` 关闭梯度记录、减少计算图开销。还需执行 `model.eval()` 切换 Dropout、BatchNorm 等层的行为：前者控制自动微分，后者控制模型的训练/推理模式。

## 三、力为什么要保留坐标求导链

以一维无量纲简谐势为例，用 $E=\frac12 kx^2$ 演示负梯度：

```python
import torch

position = torch.tensor([1.0, -2.0], requires_grad=True)
k = 2.0
energy = 0.5 * k * position.square().sum()
(gradient,) = torch.autograd.grad(energy, position)
force = -gradient
print(force)
assert torch.allclose(force, torch.tensor([-2.0, 4.0]))
```

这里输出是两个坐标的负梯度，不是已经训练好的材料力场。真实能量模型中，只有模型对坐标的计算链连续、单位对应正确，才能由能量导出力。

可对一个坐标做中心差分，固定其他坐标，检查自动微分力是否等于能量差分的负值。仓库的 MACE 硅案例已对畸变后的一个力分量走过同样的检查。这个对照能定位符号和求导链问题，参考精度要另外验证。 [有限差分与归档结果](../../机器学习势函数/基础与比较/势函数的学习对象与数学基础.md)

如果训练损失还包含力，需要继续对力求模型参数梯度，常涉及 `create_graph=True`，显存需求也会增加。不要在求力前把坐标转成 NumPy 或用 `detach()` 切断计算链。

参考：[PyTorch 自动微分教程](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)。
