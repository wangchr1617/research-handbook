# PyTorch 自定义数据集

**适用环境：已安装 PyTorch 的 Python 环境；下面只用 CPU 和标准库 CSV。**

模型不直接读取一堆计算目录，而是从 Dataset 取得一个样本，再由 DataLoader 组合成 batch。先把文件、样本和张量一一对应，再加入复杂的特征。

## 一、准备一个演示表格

先完成 [PyTorch 安装](PyTorch安装与入门.md)，新建练习目录，将下面内容保存为 `materials-demo.csv`：

```csv
feature_1,feature_2,energy_eV_per_atom
0.0,0.0,-5.0
1.0,0.0,-4.8
0.0,1.0,-5.1
1.0,1.0,-4.9
2.0,0.0,-4.6
0.0,2.0,-5.2
2.0,1.0,-4.7
1.0,2.0,-5.0
```

特征是无量纲人工数值，能量是演示标签，不是材料计算结果。真实数据还应保存样本 ID、来源和分组键，这些元信息不必全部喂给网络。

## 二、定义 Dataset

将本文两个 Python 代码块依次保存为 `dataset_demo.py`：

```python
import csv
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader, random_split

class MaterialDataset(Dataset):
    def __init__(self, path):
        with Path(path).open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        if not rows:
            raise ValueError("dataset is empty")
        self.features = torch.tensor(
            [[float(row["feature_1"]), float(row["feature_2"])] for row in rows],
            dtype=torch.float32,
        )
        self.targets = torch.tensor(
            [[float(row["energy_eV_per_atom"])] for row in rows], dtype=torch.float32
        )
        if not torch.isfinite(self.features).all() or not torch.isfinite(self.targets).all():
            raise ValueError("non-finite input")

    def __len__(self):
        return len(self.targets)

    def __getitem__(self, index):
        return self.features[index], self.targets[index]
```

`__len__` 返回样本数，`__getitem__` 返回指定样本。目标保存为 `[N,1]`，与单输出回归网络的输出形状匹配，避免 `[N]` 和 `[N,1]` 广播成意外的损失矩阵。

## 三、用 DataLoader 组成 batch

```python
root = Path(__file__).resolve().parent
dataset = MaterialDataset(root / "materials-demo.csv")
train_set, valid_set = random_split(
    dataset, [6, 2], generator=torch.Generator().manual_seed(7)
)
loader = DataLoader(train_set, batch_size=3, shuffle=True, num_workers=0)
features, targets = next(iter(loader))
print("samples:", len(dataset), "train:", len(train_set), "valid:", len(valid_set))
print("batch:", features.shape, targets.shape)
assert features.shape == (3, 2)
assert targets.shape == (3, 1)
```

执行 `python dataset_demo.py`，应得到八个样本和上述 batch 形状。`num_workers=0` 让入门示例在主进程读数据，先减少跨平台多进程因素；确需加速时再测试多个 worker，脚本入口也要按多进程要求组织。

真实数据用预先确定的分组索引创建 Subset，不直接用这里的随机划分。标准化参数只从训练子集拟合；验证集使用同一参数，但不能参与其拟合。

接着把 `loader` 接到 [模型训练循环](PyTorch模型训练与保存.md)。变长原子结构通常需要专门的图数据批处理，不能把不同原子数的坐标直接交给默认拼接。

参考：[PyTorch Dataset 与 DataLoader](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html)。
