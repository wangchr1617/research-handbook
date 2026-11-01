# scikit-learn 回归基线

**适用环境：Windows、macOS、Linux 的 Python 环境；使用 NumPy 和 scikit-learn。**

复杂模型开始之前，先训练一个简单基线。以带噪声的人工回归数据为例，比较“只预测训练集均值”和带正则化的线性模型，学会拟合、调参和评估。

## 一、安装并准备数据

```bash
python -m pip install numpy scikit-learn
```

把下面两个 Python 代码块依次保存为 `regression_demo.py`：

```python
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

rng = np.random.default_rng(7)
x = rng.normal(size=(200, 3))
y = 1.5 * x[:, 0] - 2.0 * x[:, 1] + 0.1 * rng.normal(size=200)
x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=7
)
```

这是假设样本相互独立的演示数据，目标无物理单位。真实材料数据应先按 [数据划分](数据划分与模型评估.md)确定组或时间边界，不直接照抄随机划分。

## 二、在训练部分选择超参数

```python
baseline = DummyRegressor(strategy="mean").fit(x_train, y_train)
pipeline = make_pipeline(StandardScaler(), Ridge())
search = GridSearchCV(
    pipeline,
    param_grid={"ridge__alpha": [0.01, 0.1, 1.0, 10.0]},
    scoring="neg_mean_absolute_error",
    cv=KFold(n_splits=5, shuffle=True, random_state=7),
)
search.fit(x_train, y_train)
print("selected parameters:", search.best_params_)
for name, estimator in [("mean baseline", baseline), ("ridge", search.best_estimator_)]:
    prediction = estimator.predict(x_test)
    mae = mean_absolute_error(y_test, prediction)
    rmse = np.sqrt(mean_squared_error(y_test, prediction))
    print(name, "MAE:", mae, "RMSE:", rmse, "R2:", r2_score(y_test, prediction))
assert mean_absolute_error(y_test, search.predict(x_test)) < mean_absolute_error(
    y_test, baseline.predict(x_test)
)
```

执行 `python regression_demo.py`，Ridge 在这组近似线性的数据上应明显优于均值基线。`GridSearchCV` 采用越大越好的评分约定，所以 MAE 写成负值；输出的真正误差仍用正数报告。

`StandardScaler` 放进 Pipeline，每个交叉验证训练折独立拟合，测试集不参与尺度计算。`ridge__alpha` 中前半部分是流水线里的步骤名称，后半部分是该估计器的参数。

## 三、换成自己的表格

把每个样本放一行、特征放各列，目标单独一列。排除材料标签、文件路径、作业 ID 等不该作为数值特征的元信息；这些信息用于追踪来源和分组。

先检查缺失值、样本数和特征含义，再训练。若做缺失值填补，也放到 Pipeline 的训练阶段；不能先从整张表算平均值填补，再划分测试集。

基线差并不自动说明应该换深度网络。先确认数据和评价目标，再比较模型复杂度；简单模型、数据和结果都保留，方便后续复现。

参考：[scikit-learn 入门](https://scikit-learn.org/stable/getting_started.html)、[Pipeline 与预处理](https://scikit-learn.org/stable/common_pitfalls.html)。
