# NumPy 数组与科学计算

**适用环境：Windows、macOS、Linux 的 Python 环境。**

Python 列表适合组织数据，NumPy 数组适合批量数值运算。科研代码里先看数组的形状、类型和单位，再考虑如何加速。

## 一、安装和数组形状

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

## 二、沿哪个轴计算

```python
force = np.array([[3.0, 0.0, 4.0], [0.0, 0.0, 2.0]])
magnitude = np.linalg.norm(force, axis=1)
print(magnitude)
assert np.allclose(magnitude, [5.0, 2.0])
print("max force =", magnitude.max(), "eV/angstrom")
```

`axis=1` 沿每行的三个分量求模，得到每个原子的力大小；不指定轴则可能把整个数组合成一个数。

为什么还要再取一次 `max()`？结构优化中的最大原子受力，是各原子力模的最大值。直接在原数组上取最大值，只会得到最大的带符号分量，含义不同。

## 三、广播与筛选

```python
shift = np.array([1.0, 0.0, 0.0])
shifted = positions + shift
selected = positions[magnitude > 3.0]
print(shifted)
assert selected.shape == (1, 3)
```

`shift` 的形状为 `(3,)`，NumPy 把它加到 `positions` 的每一行，这就是广播。形状从尾部维度开始匹配，因此表达式能运行之后，还需确认结果符合预期；涉及列向量时，可用 `[:,None]` 等写法明确维度。

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
