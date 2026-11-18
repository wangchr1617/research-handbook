# CASTEP 结构优化与能量–体积曲线

从已收敛的单点设置出发，先决定实验或模型要求固定哪些量。外延薄膜可能需要固定面内格矢，体相在指定外压下可做变胞优化。比较多个体积的能量时，每个体积的内部坐标弛豫应使用一致的策略。

## 一、先用固定晶胞验收原子弛豫

将[单点练习](CASTEP首个单点计算.md)的输入复制到一个新目录，改用同一个新种子名。为了观察优化，可对一条 Si–Si 键引入小扰动，同时检查对称性是否把扰动约束回去。在 `.param` 中替换任务并加入力阈值，在 `.cell` 中固定晶胞。

```text
TASK : GEOMETRYOPTIMIZATION
GEOM_FORCE_TOL : 0.02 eV/ang
```

```text
FIX_ALL_CELL : TRUE
```

查看主输出中每个几何步的电子收敛、能量和最大力，从 `.geom` 的最后一个完整几何步取晶格和坐标。固定晶胞时应核对格矢保持不变；变胞时则要同时复制同一步的格矢和坐标，避免只更新其中一项。只有电子步和几何步分别满足判据，才将结构传给能带或声子任务。选择性固定原子时查 `IONIC_CONSTRAINTS` 的方向和原子序号规则。每个受约束自由度都要和模型意图一致。

## 二、按目标选择变胞或固定体积扫描

- **零压体相**：按模型允许的晶胞自由度放开优化。检查最终应力、最大力和体积，另加高截断单点核对。有限基组误差会影响应力判读。
- **给定体积**：对一组包围能量最低点的体积生成结构。保持比例缩放时，格矢乘 $(V/V_0)^{1/3}$。固定每个晶胞再弛豫内部坐标，统一按每原子或每化学式单元记录能量和体积。
- **拟合**：检查最低点位于数据区间内，再比较拟合窗口。体模量满足 $B=V\,\mathrm d^2E/\mathrm dV^2$，若能量和体积用 eV 与 Å³，$1\ \mathrm{eV/Å^3}\approx160.22\ \mathrm{GPa}$。不同归一化的能量和体积不能混用。

仓库的[硅状态方程案例](../VASP/结构与能量/VASP能量体积曲线拟合.md)用同一硅相的五个体积演示如何读拟合。以其中 $1.06V_0$ 为例，格矢只乘 1.0196。若试算里最低能量还在扫描端点，沿能量下降方向补点，再比较拟合窗口对 $V_0$ 和 $B$ 的影响。迁移到 CASTEP 时，重新按所用势和 k 网格计算各点。

参考 [CASTEP 几何优化练习](https://castep-docs.github.io/workshop/workshop/03_geometry/)、[约束](https://castep-docs.github.io/castep-docs/documentation/Geometry_Optimisation/constraints/)及[输出文件](https://castep-docs.github.io/castep-docs/documentation/Geometry_Optimisation/files/)。
