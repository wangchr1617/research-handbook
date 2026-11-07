# Packmol 周期距离与原子区域约束

**适用环境：Packmol 21.2.3；Python 3.10+ 与 NumPy 用于分析。**

本例生成两个小型初始构型：32 个水的周期盒，以及按 O/H 位置定义方向的 16 水层。它们用于检查区域、周期距离和原子顺序，不对应平衡液体或真实界面性质。

## 生成与运行

从仓库根目录运行，工作目录应尚不存在：

```bash
python examples/packmol-regions/prepare.py --work-root /tmp/packmol-regions
PACKMOL_EXEC=/path/to/packmol bash /tmp/packmol-regions/run.sh
python examples/packmol-regions/analyze.py \
  --work-root /tmp/packmol-regions --output-dir /tmp/packmol-regions-analysis
```

将可执行文件路径换成当前环境的 Packmol。生成器同时保存水模板、输入、分子数和固定种子。运行脚本使用 `-i packmol.inp -o packed.xyz`，因此最终输出覆盖输入文件里写的 `unused.xyz`；这一路线需要 v21.1.0 或更新版本。

已有[数值表](analysis.json)、[周期结构](periodic.xyz)和[定向层结构](oriented-layer.xyz)可直接查看。XYZ 的坐标单位为 Å，分子按 O/H/H 顺序排列，文件本身不提供完整力场或拓扑。周期盒长另保存在数据和输入说明中。

## 周期水盒

水的模板为 O–H 0.96 Å、H–O–H 104.5°。输入用 `pbc 12.0 12.0 12.0`，放入 32 个水，距离约束为 2 Å，固定种子 314159。此粒子数用于几何演示，没有以某个实验密度标定。

分析器对不同分子的原子对同时计算直接距离和最小镜像距离。在正交盒中，位移按 $\Delta x_k-L_k\operatorname{nint}(\Delta x_k/L_k)$ 处理；这里的写法不直接用于任意斜晶胞。

本组最短直接距离和全局最小镜像距离都约为 2.17834 Å，但并非没有周期作用：共有 2558 个不重复的跨镜像原子对，最近的跨镜像距离约为 2.19861 Å。只比较两个全局最小值是否不同，不能判断程序有没有检查镜像。

## 定向水层

每个水的所有原子先限制在 $[0,12]\times[0,12]\times[0,4]$ Å 盒内，再加两组局部规则：O 原子处于 $2.0\le z\le2.2$ Å，两个 H 原子处于 $z\ge2.5$ Å。它们与全局条件共同作用，使 H 一侧大体朝向 +Z。

原生结果的 O 范围为 2.0–2.2 Å，最低 H 坐标为 2.5 Å，分子间最近原子距离约为 2.00000 Å。约束指定的是原子区域，没有生成真实的水表面、外场平衡取向或相应能量。

两组结果的水分子内部距离与模板的最大差异均小于 $10^{-6}$ Å。若改变模板或区域，需重新检查几何是否可行；不能只增加优化循环来解决互相矛盾的条件。

完整规则和拓扑对应见[Packmol 空间与周期边界](../../notes/Packmol/空间分区、周期边界与拓扑对应.md)，完整分子壳层的提取见[甲烷水球](../solvent-shell/README.md)。
