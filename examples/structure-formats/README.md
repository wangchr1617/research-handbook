# 结构文件的字段保留与转动常数

**适用环境：通用；Python、ASE、NumPy、SciPy。**

本例用同一份水分子几何演示扩展 XYZ 字段、mol2 连接表与电荷，以及同位素质量对转动常数的影响。周期数据保留见 [XYZ 与扩展 XYZ](../../notes/计算化学/XYZ与扩展XYZ的字段和单位.md)，模型解释见[实验结构与计算模型](../../notes/计算化学/从实验结构到计算模型.md)。

## 数据和复现

输入来自[溶剂参数案例](../orca/minimal/solvation-parameters/README.md)的 `analysis.json`，包括 ORCA B3LYP/G（VWN3）/def2-TZVP 气相优化水坐标和对应 Multiwfn CM5 电荷。CM5 未乘缩放系数，三个电荷为 `-0.6389055132、0.3194527564、0.3194527568 e`。本例只复用这些数据，不重新计算波函数。

在已具备 `requirements.txt` 依赖的 Python 环境中，从本目录运行：

```bash
python3 analyze.py --output-dir /tmp/structure-formats-new
```

输出目录须尚不存在。脚本按仓库相对位置寻找输入，使用 ASE 内置扩展 XYZ 读写器；示例结果采用 ASE 3.29.0。`analysis.json` 记录源文件摘要、字段含义及使用的同位素原子质量。

## 比较格式保留了什么

| 文件 | 包含的信息 |
| --- | --- |
| [water.extxyz](water.extxyz) | 元素、坐标、CM5 电荷、身份标签、斜晶胞、部分周期方向和电子能 |
| [reordered.extxyz](reordered.extxyz) | 同一结构，将身份和电荷列放在坐标之前，用模式声明实际顺序 |
| [water-plain.xyz](water-plain.xyz) | 显式普通 XYZ，只保留元素与坐标 |
| [water.mol2](water.mol2) | SYBYL 类型、两根 O–H 键、子结构及 `USER_CHARGES` CM5 电荷 |
| [water-cell.mol2](water-cell.mol2) | 另加 P1 `CRYSIN` 晶胞段，用于完整周期晶胞信息演示 |
| [analysis.json](analysis.json) | 字段核对结果、惯量、转动常数及模型定义 |

斜晶胞的行矢量为 `(7,0,0)`、`(1.5,8,0)`、`(0.7,1.2,9)` Å，体积 504 Å³，是人为加入的格式测试盒子。扩展 XYZ 的周期方向为 `T F T`；mol2 晶胞文件演示完整周期晶胞元数据，不能把它当作保留了这一部分周期定义。两者均不表示实际水晶体或周期量化结果。

ASE 能按两种 `Properties` 顺序读回同样的坐标、身份和电荷。`atom_id` 的 101–103 是本例添加的身份标签，与 mol2 中 1–3 的编号按原子顺序对应。其写入器会优先排列元素、坐标，因此异序版本由脚本按显式模式单独生成，再交给 ASE 读入。普通 XYZ 版本丢失晶胞、周期方向、电荷、身份和电子能；之后再转换回扩展 XYZ，缺失数据不会自动恢复。

扩展 XYZ 的 `energy` 已由原生 Hartree 换算为 ASE 的 eV 约定；`energy_unit=eV` 仅说明该字段。写入器的小数位数影响往返误差，比较时保留容差。本例原生 CM5 数值保存在 mol2 和源 JSON 中，扩展 XYZ 的八位小数会引入约 $10^{-9}$ e 量级的逐原子舍入差。

mol2 文件的类型和连接表描述水的几何拓扑，没有给出完整 MM 力场。只读 `audit_mol2` 对单体系、显式元素类型和本例晶胞段做保守检查；不推断电荷、不感知芳香性、不修复外部力场方言，也不改写输入。实际读取软件是否保留电荷和晶胞字段，需用往返数据核对。

## 相同坐标，不同同位素质量

把坐标保持不变，用指定的 $^{16}$O、$^1$H 和 $^2$H 同位素原子质量计算惯性张量，再求刚性转子的三个常数。质量采用 NIST 表中的 [$^1$H、$^2$H](https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=H)及 [$^{16}$O](https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=O)数值，使用原子质量约定而非裸核质量：

| 同位素质量组合 | A（MHz） | B（MHz） | C（MHz） |
| --- | --- | --- | --- |
| H₂O | 826809.950 | 428407.386 | 282191.362 |
| D₂O | 459953.369 | 214368.356 | 146220.185 |

表中从 u 换算为 kg 采用 [CODATA 2022](https://physics.nist.gov/cuu/pdf/wallet_2022.pdf) 的 `1 u = 1.66053906892×10⁻²⁷ kg`。复算时记录常数库版本；使用较旧的换算值可造成末位差异，不应通过调整几何来对齐这些差异。

这组数值只用于分清质量与几何的贡献，不是实验有效转动常数。原坐标属于给定理论方法的气相优化结果，替换质量时没有重算几何、振动平均或非 Born–Oppenheimer 修正。实验 $B_0$ 与平衡 $B_e$ 的比较还需匹配振转修正、同位素及测量条件。
