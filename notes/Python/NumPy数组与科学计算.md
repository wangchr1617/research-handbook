# NumPy 数组与科学计算

**适用环境：Windows、macOS、Linux 的 Python 环境。**

结构优化结束后，若程序的停止条件是最大原子受力，可以拿导出的力表再核对一次。每行是一个原子，三列是力分量。把最大分量直接当最大原子受力，会得到另一个量。下面用两个原子的教学数据贯穿形状、沿轴计算和筛选。

## 一、先把数组的行列对回原子和坐标

先准备 [Python 环境](../../getting-started/pip与uv安装与使用.md)，在目标环境执行：

```bash
python -m pip install numpy
python -c "import numpy; print(numpy.__version__)"
```

将本文代码依次放到 `numpy_demo.py`，执行 `python numpy_demo.py`：

```python
import numpy as np

positions = np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 2.0]])
print(positions.shape, positions.dtype)
print(positions[0])
print(positions[:, 2])
assert positions.shape == (2, 3)
```

`(2,3)` 表示两个原子、每个三个坐标；`[:,2]` 取所有行的第三列。这个例子的坐标单位假设为 Å，实际文件的单位要从计算软件说明确认。

## 二、先算每个原子的力模，再取最大值

```python
force = np.array([[3.0, 0.0, 4.0], [0.0, 0.0, 2.0]])
magnitude = np.linalg.norm(force, axis=1)
print(magnitude)
assert np.allclose(magnitude, [5.0, 2.0])
print("max force =", magnitude.max(), "eV/angstrom")
```

`axis=1` 沿每行的三个分量求模，得到每个原子的力大小；不指定轴则可能把整个数组合成一个数。

为什么还要再取一次 `max()`？本例两个原子的力模分别为 5 和 2 eV/Å，最大原子受力为 5 eV/Å，直接执行 `force.max()` 则得到 4 eV/Å。如果程序报告的是最大力分量或对自由度另有约束，要按该程序的定义复核。

## 三、平移坐标并定位高受力原子

```python
shift = np.array([1.0, 0.0, 0.0])
shifted = positions + shift
selected = positions[magnitude > 3.0]
print(shifted)
assert selected.shape == (1, 3)
```

`shift` 的形状为 `(3,)`，NumPy 把它加到 `positions` 的每一行，这就是广播。形状从尾部维度开始匹配，因此表达式能运行之后，还需确认结果符合预期；涉及列向量时，可用 `[:, None]` 等写法明确维度。`magnitude > 3.0` 选出第一个原子的坐标。掩码只有在力表与坐标表逐行对应时才有意义。若其中一张表曾重新排序，先按原子 ID 对齐两张表。

## 四、切片可能共享内存

```python
values = np.arange(6.0)
view = values[:3]
view[0] = 99.0
assert values[0] == 99.0
independent = values[:3].copy()
independent[0] = -1.0
assert values[0] == 99.0
```

基本切片常得到视图，修改它会影响原数组。要独立处理时用 `.copy()`。这和普通 Python 列表切片的直觉不同，保存原始数据时尤其要注意。

## 五、数值比较与缺失值

```python
a = np.array([0.1 + 0.2, np.nan])
assert np.isclose(a[0], 0.3)
print(np.isfinite(a))
```

浮点计算通常用 `isclose` / `allclose` 按合适容差比较，不逐位要求相等。出现 NaN 时先检查来源；`nanmean` 会忽略缺失值，只有在这符合分析定义时才使用，不能用它隐藏失败计算。

加载文本数组可用 `np.loadtxt`，保存时用 `np.savetxt` 并写表头和单位，完整练习见 [科研数据读写](科研数据读写与绘图.md)。参考：[NumPy 官方基础教程](https://numpy.org/doc/stable/user/absolute_beginners.html)。
