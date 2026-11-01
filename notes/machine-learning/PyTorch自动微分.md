# PyTorch 自动微分

**适用环境：已安装 PyTorch 的 Python 环境；本例在 CPU 运行。**

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

## 二、梯度为什么需要清零

每次反向传播会累加梯度。训练时通常每个 batch 先执行 `optimizer.zero_grad(set_to_none=True)`，再前向计算、反向传播和更新。只有明确进行梯度累积时，才有意跨 batch 保留梯度。

推理时既不需要梯度，也不需要保留训练计算图，可使用 `torch.inference_mode()`；模型仍需执行 `model.eval()` 切换 Dropout、BatchNorm 等层的行为。这是两个不同操作。

## 三、能量对坐标的导数

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

如果训练损失还包含力，需要继续对力求模型参数梯度，常涉及 `create_graph=True`，显存需求也会增加。不要在求力前把坐标转成 NumPy 或用 `detach()` 切断计算链。

参考：[PyTorch 自动微分教程](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)。
