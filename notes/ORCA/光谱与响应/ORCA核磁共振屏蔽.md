# ORCA 核磁共振屏蔽

**适用环境：Linux + PBS 运行计算；Windows / macOS / Linux 可准备输入与分析结果。**

ORCA 给水中两个 H 都报出约 31.093 ppm。能否直接把这个数画在实验化学位移轴上？先从原生输出确认它是屏蔽张量的各向同性值，再用同一约定计算参考物，才能得到可比较的化学位移。

## 一、屏蔽与化学位移怎样联系

各向同性屏蔽为屏蔽张量三个主值的平均，常以 ppm 报告。简单参考关系可写作 δ≈σref−σsample，具体转换还受参考定义、实验尺度及拟合方式影响。

屏蔽对核附近电子结构、几何、基组与环境敏感。重元素附近还要注意相对论及 SOC 对性质的影响；普通轨道基组未必像专用屏蔽基组那样适合核区响应。

## 二、计算水中 H、O 的屏蔽

本例以固定构型的中性水分子为对象，采用 PBE0/pcSseg-1 计算 H 和 O 的核屏蔽。pcSseg-1 是专门针对屏蔽性质设计的基组；这里不做几何优化，以便把注意力集中在响应计算模块的设置上。

[案例目录](../../../examples/orca/minimal/nmr-shielding)包含以下科学输入：

[shielding.inp](../../../examples/orca/minimal/nmr-shielding/shielding.inp)、[stages.json](../../../examples/orca/minimal/nmr-shielding/stages.json)、[structure.xyz](../../../examples/orca/minimal/nmr-shielding/structure.xyz)。

分子结构存放在坐标文件或各输入文件的原子/晶胞段中，`stages.json` 用于列出计算阶段。配套脚本中，[run.py](../../../examples/orca/minimal/nmr-shielding/run.py) 按顺序组织计算任务，[job.pbs](../../../examples/orca/minimal/nmr-shielding/job.pbs) 用于提交作业，[postprocess.py](../../../examples/orca/minimal/nmr-shielding/postprocess.py) 负责检查结果并绘图。

## 三、核选择与输入顺序

加载 ORCA 及其匹配的 MPI 环境，`ORCA_EXEC` 可指定驱动绝对路径。每步计算使用 1 个进程和 1000 MB 主工作内存，直接调用 ORCA 驱动，外部不加 `mpirun`；所需基组由程序自带。

| 设置 | 作用 |
| --- | --- |
| `NMR` 与 `%eprnmr` | 启动并指定核屏蔽性质 |
| `Nuclei = all H/O { shift }` | 选择元素与目标性质；此处 shift 请求的是屏蔽相关输出 |
| 坐标块顺序 | **坐标必须位于 `%eprnmr` 核选择块之前** |
| `TightSCF` | 减少电子响应中的数值误差 |

若输出只有能量而没有目标核的响应，应检查核选择与方法支持情况。

在干净案例目录安装[Python 依赖](../../../examples/orca/minimal/nmr-shielding/requirements.txt)并提交：

```bash
python3 -m pip install -r requirements.txt
qsub job.pbs
```

PBS 中的资源语法和软件加载方式按集群调整。计算结束后自动执行后处理；若只分析已保存的结果，运行 `python3 postprocess.py`。各阶段独立保存输出，便于定位失败步骤。

## 四、先核对原子，再解释屏蔽值

原生屏蔽汇总表给出两个 H 的各向同性屏蔽均为约 31.093 ppm，O 约为 337.320 ppm；对称等价的 H 给出相同数值，正好可以作为一项简单的一致性检查。

图画的是屏蔽，不是以 TMS 为零点的化学位移，也不是含线宽的实验 NMR 谱。后处理保留核编号、元素、各向同性值和各向异性值，避免只凭元素名丢失原子对应关系。

![ORCA核磁共振屏蔽结果](../assets/nmr-shielding.png)

图由案例后处理脚本读取实际计算输出生成。

本机复跑中，一个 H 的屏蔽张量主值为 23.766、25.352 和 44.161 ppm，平均即 31.093 ppm，另一个 H 给出同样的结果。若比较一组同核样品，还要保存参考物的结构、方法和环境。在简单差值约定下，样品的屏蔽值越大，换算出的化学位移就越小，这一符号关系也可以用来核对作图是否正确。

## 五、扩展到实际研究

实际样品需考虑构象、溶剂、温度平均和参考物，样品与参考应采用一致计算方案。查看张量和轨道响应应优先使用 ORCA 原生输出；Multiwfn 可补充分析电子结构，但不能仅由静态电荷密度替代完整磁响应。

参考：[ORCA NMR 手册](https://www.faccts.de/docs/orca/6.1/manual/contents/spectroscopyproperties/nmr.html)。
