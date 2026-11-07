# 绘图

MSD 单文件分量和多文件比较均使用 `plot_msd.py`，通过 `--columns` 指定零起始列号，并明确设置时间单位和换算系数。

```bash
python scripts/plotting/plot_msd.py msd.out --columns 1 2 3 --time-unit ps
python scripts/plotting/plot_msd.py MSD_1.dat MSD_2.dat --skiprows 1 --columns 4 --time-unit fs
```

## 文件

- [plot_msd.py](plot_msd.py)：绘制单文件分量或多文件总 MSD（依赖 NumPy、Matplotlib）。
- [plot_pca.py](plot_pca.py)：对结构描述符进行 PCA 分析及绘图。
- [plot_phonon_band.py](plot_phonon_band.py)：绘制声子能带。

`plot_pca.py` 同时包含 NEP 描述符计算、标准化与最远点采样，运行前须核对模型、输入和采样参数。

对其他绘图任务，先明确输入列、单位、归一化和预期结果，再编写并用小样本验证。基础示例见[科研数据读写与绘图](../../notes/Python/科研数据读写与绘图.md)。与完整案例绑定的重绘脚本保留在各案例目录。
