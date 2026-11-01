# 第一个小案例：计算并检查 RMSE

**适用环境：Windows / macOS / Linux（Python 3）。**

用三行人工构造的数据练习读取文件、计算 RMSE 和核对单位，无第三方依赖。

在仓库根目录运行：

```bash
python3 examples/rmse/run.py
```

脚本读取同目录下 `data.csv` 的 `reference` 和 `prediction` 两列，使用 RMSE = sqrt(mean((prediction - reference)^2)) 计算误差。本例两列单位均为 eV/atom，因此输出单位也是 eV/atom。

预期输出：

```text
Samples: 3
RMSE: 1.000000 eV/atom
```

三行预测误差分别为 +1、-1、+1，因此 RMSE 为 1。可以修改一行预测值后重新运行，并手算核对。

Windows 若使用 `python` 命令，将上面的 `python3` 替换为 `python`。更多数据处理工具见 [科研脚本](../../scripts/README.md)。
