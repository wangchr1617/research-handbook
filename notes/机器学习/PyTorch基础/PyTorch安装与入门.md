# PyTorch 安装与入门

**适用环境：Windows、macOS、Linux；先用 CPU 跑通，GPU 按设备选择 CUDA 或 MPS。**

PyTorch 用张量表示数据，用自动微分计算梯度，再通过优化器更新模型。先安装一个独立环境，跑通小例子，再使用课题组的训练代码。

## 一、安装环境

没有 Python 时先按 [Conda 环境准备](../../../getting-started/Anaconda、Miniconda、Mamba安装与使用.md)安装 Miniconda 或 Miniforge。在对应 Prompt 或终端执行：

```bash
conda create -n pytorch-learn python=3.12
conda activate pytorch-learn
python -m pip --version
```

打开 [PyTorch 官方安装页](https://pytorch.org/get-started/locally/)，选择稳定版、操作系统、Pip、Python 和计算平台，使用它生成的命令。先学基础不必购买 GPU。

Mac 常用安装方式：

```bash
python -m pip install torch torchvision
```

Windows / Linux 仅用 CPU 时可选官方 CPU wheel：

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Linux NVIDIA GPU 用户先在获准节点检查 `nvidia-smi`，再按官方选择器和集群驱动支持范围选 CUDA 构建。`nvidia-smi` 显示的 CUDA 版本是驱动能力信息，不等于当前环境安装的工具包。Mac 不装 CUDA，Apple Silicon 可使用 MPS。

## 二、确认解释器与设备

将下面内容保存为 `check_torch.py`，在该目录执行 `python check_torch.py`：

```python
import sys
import torch

print("Python:", sys.executable)
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("MPS available:", torch.backends.mps.is_available())
device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)
x = torch.arange(6, dtype=torch.float32, device=device).reshape(2, 3)
print("Device:", x.device)
print(x @ x.T)
```

结果应是 `[[5, 14], [14, 50]]`，显示格式随设备不同。CUDA / MPS 返回 `False` 时仍可使用 CPU，先完成这个计算再学训练循环。模型参数和参与同一次运算的张量放在同一设备。

## 三、张量里最常看什么

```python
import torch

x = torch.randn(8, 4)
print(x.shape, x.dtype, x.device)
y = torch.tensor([0, 1, 0, 1, 0, 1, 0, 1], dtype=torch.long)
print(y.shape, y.dtype)
```

这里有 8 个样本、每个 4 个特征；分类标签是一维整数。浮点特征常用 `float32`，分类标签常用 `long`。维度写对了，损失函数才知道如何比较预测与标签。

以材料数据为例，能量是 eV 还是 eV/atom、应力是什么单位，都要在读入数据时统一。张量只存数字，不会替你判断物理单位。

接下来阅读 [自动微分](PyTorch自动微分.md)、[模型训练与保存](PyTorch模型训练与保存.md)。先不引入额外训练框架，掌握训练循环后再使用封装。

参考：[官方张量教程](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)、[MPS 说明](https://docs.pytorch.org/docs/stable/notes/mps.html)。
