# VASP 训练数据准备

**适用环境：Linux（VASP 标注）；Windows / macOS / Linux（结构处理与数据检查）。**

先明确势函数要解决的任务，再确定采样范围。平衡晶体、缺陷、表面、液体或反应环境需要不同的构型覆盖；采样方法的成本与最终 DFT 标签精度也应分开考虑。

## 采样与统一标注

可从小位移、小应变和目标条件下的 MD 结构开始，筛除原子重叠等明显不合理构型，再加入模型误差较大的结构。扰动幅度和轨迹抽样间隔取决于体系相关时间与目标环境，不将固定的百分比、位移幅度或 `0.1 ps` 当作通用标准。随机构型方法可参考 [RAG 原始论文](https://pubs.acs.org/doi/10.1021/acs.jpcb.0c05075)。

标注使用一致的势、泛函、截断能、电子收敛和能量定义。对于受力或应力敏感的任务，应直接检查这些目标量的收敛；不能只凭总能量平稳或某个统一 `KSPACING` 判断标签精度。

[批量单点案例](../../examples/vasp/minimal/batch-single-points/)提供两个硅构型的计算与导出，PBS 步骤见[批量计算](VASP批量计算.md)。它用于演示格式和标签核对，训练势函数还需扩充构型覆盖并保留独立测试集。

## 使用通用导出器

在包含纯 DFT 子任务的目录中执行仓库脚本：

```bash
python3 scripts/structure/vasp2xyz.py calculations -o train.xyz --frames all --converged --energy free
```

[vasp2xyz.py](../../scripts/structure/vasp2xyz.py)优先读取 `vasprun.xml`，必要时回退 OUTCAR；`--frames last` 只取每个任务的最后一帧。示例命令从仓库根目录执行，`calculations` 替换为自己的计算目录。

默认能量为 TOTEN 自由能，单位 eV；`--energy zero` 可选择零温外推能量，但整个数据集应保持同一定义。力单位为 eV/Å。位力采用：

$$\mathbf W=-V\boldsymbol\sigma_{\mathrm{ASE}},$$

单位为 eV。VASP 原始应力通常以压缩为正、单位为 kBar，ASE 应力则采用相反符号并转换为 eV/Å³；不能直接把应力数值填入位力字段。

案例[后处理](../../examples/vasp/minimal/batch-single-points/postprocess.py)将导出的能量、力及位力与原始 XML 交叉核对，并检查周期边界和帧数。没有应力数据时，可显式使用 `--no-virial`，不要补零伪装成完整标签。

## 数据来源与划分

`--converged` 会核对电子迭代步数和帧数；还应检查异常终止、错误信息及代表性结构，不能只依靠一个筛选开关。

导出器会拒绝含 `ML_LMLFF` 的目录，避免把 MLFF 预测帧混进 DFT 标签。若用 MLFF 采样，可选择其中的结构重新做独立 DFT 标注；训练数据库和预测轨迹则应按各自格式处理。

按独立轨迹、结构族或采样条件划分训练、验证和测试集，避免高度相近的相邻帧同时出现在训练与测试中。报告模型误差时，说明数据来源、能量参考和单位，而不是只给一个总 RMSE。
