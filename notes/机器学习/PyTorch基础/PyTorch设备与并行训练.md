# PyTorch 设备与并行训练

**适用环境：CPU / Apple Silicon Mac（MPS）/ Linux NVIDIA GPU；多卡示例仅用于已有 GPU 资源分配的 Linux 节点。**

先在 CPU 或单卡上核对训练流程，再做混合精度和多卡。GPU 数量增加，不会自动解决数据划分、损失定义或单位错误。

## 一、把模型和数据放在同一设备

下面的小例子可以在 CPU、MPS 或 CUDA 中选择实际可用的设备：

```python
import torch
from torch import nn

device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)
model = nn.Linear(3, 1).to(device)
x = torch.randn(4, 3, device=device)
y = torch.randn(4, 1, device=device)
loss = nn.MSELoss()(model(x), y)
loss.backward()
print(device, loss.item())
assert torch.isfinite(loss)
```

`.to(device)` 返回迁移后的张量，写成 `x = x.to(device)`，不只调用后丢弃返回值。Mac 的 MPS 和 NVIDIA CUDA 是不同后端，不能将 CUDA 专用参数照搬到 MPS。

## 二、单卡先看显存和批大小

在已获准的 Linux GPU 节点用 `nvidia-smi` 查看分配给自己的卡和使用情况，再运行训练。脚本读取 `torch.cuda.is_available()` 确认当前环境确实能调用 CUDA。

先减小 batch size 看流程是否正常。梯度累积可以分多次前向、反向后再更新，但损失缩放、最后不足一组的 batch 和调度器更新次数都要处理清楚。

CUDA 混合精度通常使用 `torch.autocast` 和 `torch.amp.GradScaler`。是否启用、采用 float16 还是 bfloat16，要结合硬件与数值稳定性判断；先比较同一数据上的损失和梯度，参考 [官方 AMP 示例](https://docs.pytorch.org/docs/stable/notes/amp_examples.html)。

## 三、多卡 DDP 需要准备什么

PyTorch 的 DistributedDataParallel（DDP）通常采用每张 GPU 一个进程。每个进程有自己的模型副本，通过通信同步梯度。

| 部分 | 要做的事 |
| --- | --- |
| 启动 | 在调度器已经分配的节点上启动多个进程 |
| 设备 | 按 `LOCAL_RANK` 选择本进程的 GPU |
| 模型 | 初始化进程组后，用 DDP 包装模型 |
| 数据 | 使用 DistributedSampler 划分样本，每轮调用 `set_epoch` |
| 保存 | 通常只让 rank 0 保存模型，避免并发覆盖 |
| 指标 | 聚合各进程的统计量，不能只看某张卡的局部结果 |

DDP 不会替你自动拆分输入数据。同一个 batch 被所有进程重复训练时，即使 GPU 都在忙，也不代表数据并行配置正确。先用 [官方 DDP 教程](https://docs.pytorch.org/tutorials/beginner/ddp_series_theory.html)的小例子核对，再接入自己的模型。

PBS 集群必须先按 [PBS 笔记](../../../getting-started/PBS作业管理系统使用.md)与管理员说明申请 GPU，具体 GPU 资源语法以本站配置为准。不在登录节点试启动多卡，也不把队列名字里有 `gpu` 当作已分配到卡。

## 四、记录可复现的条件

```bash
python -m pip freeze > requirements.txt
nvidia-smi > gpu-info.txt
```

第二条只在 NVIDIA GPU 节点执行。再记录随机种子、数据版本、划分、全局 batch size、进程数、精度与检查点。固定种子有助于比较，跨硬件与版本的逐位一致性仍不能默认保证。

设备切换见 [MPS 文档](https://docs.pytorch.org/docs/stable/notes/mps.html)，安装条件见 [PyTorch 入门](PyTorch安装与入门.md)。
