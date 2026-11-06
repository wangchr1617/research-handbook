# Python 基础与脚本运行

**适用环境：Windows、macOS、Linux；示例使用 Python 3.10 及以上。**

先学会运行一个 `.py` 文件，再逐步加入变量、循环和函数。科研脚本不必一开始写得复杂，先让每一步的输入、单位和输出清楚。

## 一、准备解释器并运行文件

没有 Python 时先按 [Conda](../../getting-started/Anaconda、Miniconda、Mamba安装与使用.md)或 [pip 与 uv](../../getting-started/pip与uv安装与使用.md)准备独立环境。打开终端并激活环境：

```bash
python --version
python -c "import sys; print(sys.executable)"
```

用 VSCode 新建 `hello.py`，保存为纯文本，不要变成 `hello.py.txt`：

```python
material = "GeTe"
energy_ev = -10.25
atoms = 2
print(f"{material}: {energy_ev / atoms:.3f} eV/atom")
```

终端用 `cd` 进入文件目录，运行 `python hello.py`，应输出 `GeTe: -5.125 eV/atom`。代码是在当前工作目录运行，不能仅凭编辑器打开了文件就认为终端也在同一目录。

## 二、常见数据类型

```python
name = "GeTe"                         # 字符串
atoms = 2                             # 整数
energy = -10.25                       # 浮点数
converged = True                      # 布尔值
energies = [-10.1, -10.2, -10.25]      # 列表
record = {"name": name, "atoms": atoms, "energy_ev": energy}
print(energies[-1])
print(record["name"])
```

列表按顺序存数据，下标从 `0` 开始，`[-1]` 是最后一项。字典用键保存信息，适合把数值与单位、材料名称对应起来。`=` 是赋值，`==` 才是比较。

## 三、循环与判断

```python
energies = [-10.1, -10.2, -10.25]
for step, energy in enumerate(energies, start=1):
    if energy < -10.15:
        print(step, energy)
```

应输出第 2、3 步。冒号后面的代码用缩进表示归属，通常每层四个空格。不要混用 Tab 与空格，也不要把中文标点放进 Python 语法位置。

## 四、把重复计算写成函数

```python
def energy_per_atom(energy_ev, atoms):
    """总能量为 eV，原子数必须为正。"""
    if atoms <= 0:
        raise ValueError("atoms must be positive")
    return energy_ev / atoms

assert energy_per_atom(-10.0, 2) == -5.0
print(energy_per_atom(-10.0, 2))
```

`return` 返回结果，`print` 只是显示结果。把参数传给函数比依赖隐藏的全局变量更容易理解。单位写入变量名和函数说明，避免同一个 `energy` 一会儿表示总能量、一会儿表示每原子能量。

## 五、读懂错误位置

脚本出错时先看 traceback 最后一段的异常类型，再回到对应文件和行号。`NameError` 常是变量未定义，`FileNotFoundError` 常是路径不对；保留完整错误向师兄师姐提问即可，不要求一开始自己解决所有问题。

`import` 用于引入模块，例如 `import math`。脚本不要命名为 `numpy.py`、`torch.py` 或 `csv.py`，以免遮住要导入的同名库。

接下来阅读 [NumPy 数组](NumPy数组与科学计算.md)和 [数据读写与绘图](科研数据读写与绘图.md)。更完整的语法见 [Python 官方教程](https://docs.python.org/3/tutorial/)。
