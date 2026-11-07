# NaCl 的差分电荷密度

参考态、参数、PBS 步骤和结果图见[笔记](../../../../notes/VASP/电子结构与成键/VASP差分电荷密度.md)。准备按 `POTCAR.spec` 排列的授权势，加载 VASP、Multiwfn 与 Python 依赖后，执行 `qsub job.pbs`。

`run.py` 分别计算整体和两个固定位置的中性周期片段；`postprocess.py` 检查网格与结构、调用 Multiwfn 相减并检查电子数，`plot.py` 绘制实际网格切面。已有三组输出时运行 `python3 postprocess.py`。工具不在 PATH 时设置 `VASP_EXEC`、`MULTIWFN_EXEC`。

已有单场 `cdd.cub` 时，可沿第三网格方向对应的晶面法向绘制曲线：

```bash
python3 plane_profile.py cdd.cub --density-unit e/bohr3 --axis 3
```

[plane_profile.py](plane_profile.py)输出平面平均、截面积分和累计电子数，保留斜晶胞的面积与法向高度。输入为 Multiwfn 导出的原子单位密度；其他来源需按实际单位设置。已保存的[数值表](cdd-plane-profile.dat)、[科学元数据](cdd-plane-profile.json)及结果图的解释见[共通方法笔记](../../../../notes/计算化学/密度差、平面平均与电荷位移.md#用已有-nacl-密度结果对照)。
