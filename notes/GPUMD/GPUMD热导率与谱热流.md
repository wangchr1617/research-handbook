# GPUMD 热导率与谱热流

GPUMD 可用平衡态热流涨落、非平衡温度梯度或均匀驱动计算热输运。对于大周期晶体，HNEMD 在体系内加一个小的均匀驱动场 $\mathbf F_{\mathrm e}$，从诱导的热流求热导率，不需要在盒子两端设置冷热浴。

## 一、根据热流和温差的来源选方法

| 方法 | 读出量 | 主要检查 |
| --- | --- | --- |
| EMD | 热流自相关的 Green–Kubo 积分 | 衰减时间、积分平台、采样误差 |
| NEMD | 稳态热通量与温度梯度或温度跃变 | 驱动强度、截面、传热路径与长度效应 |
| HNEMD | 均匀弱场诱导的热流 | 场强线性区、体积、生产段与独立种子 |
| 谱热流 | 基于维里–速度相关函数的频率分解 | 时间采样、频率分辨率、频谱积分与总输运量 |

若用广延热流 $\mathbf J$，HNEMD 的线性响应关系为 $\langle J_\alpha\rangle/(TV)=\sum_\beta\kappa_{\alpha\beta}F_{{\rm e},\beta}$。二维材料还需报告有效厚度，或按二维片层系数给出不依赖厚度的归一化结果。

## 二、沿 300 K 输入找到热导率分量

仓库的 [300 K 输入](../../examples/gpumd/thermal-conductivity/300K/run.in) 用 1 fs 步长先平衡 1 ns，再驱动 20 ns。`compute_hnemd 1000 0 0 2e-5` 沿 $z$ 加 $2\times10^{-5}$ Å⁻¹ 的均匀场，每 1,000 步输出一次，因此生产段的 20,000 行各相隔 1 ps。按输入的施场方向和文档列定义，[归档输出](../../examples/gpumd/thermal-conductivity/300K/kappa.out) 第 5 列是 $\kappa_{zz}$。换用沿 $x$ 施场的三维体系时，按同一列定义将前两列相加得到 $\kappa_{xx}$。 [GPUMD 输出列](https://gpumd.org/gpumd/output_files/kappa_out.html)

按 [HNEMD Notebook](../../examples/gpumd/thermal-conductivity/HNEMD热导率计算.ipynb) 对第 5 列做累计平均，整段均值约为 2.13 W/(m·K)。把同一列按 5 ns 分块，四段均值依次约为 2.63、2.51、2.13 和 1.28 W/(m·K)。这组数能用来核对取列和时间轴，也提示后半段仍在拉低均值。要报告材料热导率，应使用独立种子估计统计误差，并用几档场强检查是否处在线性响应区。复跑时还要配齐相符的势文件，并核对势在目标温压与晶相下的表现。归档输入采用 `npt_scr`，设计新的生产段时可对照 GPUMD 的 Nosé–Hoover chain 建议。 [GPUMD 热输运文档](https://gpumd.org/theory/heat_transport.html)

## 三、有了总热导率再看热流来自哪些频段

需要频率分解时，在生产段用 `compute_shc` 计算维里–速度相关函数和谱热流。以这份沿 $z$ 施场的输入为例，输运方向参数取 2。相关时间窗由采样间隔和相关步数决定，调大频率网格点数无法补足相关时间。检查频率轴是否由角频率除以 $2\pi$ 得到，再用同一驱动方向和归一化比较谱积分与总热导率。谱峰可定位主要贡献频段，若要归因到特定声子支，还需模态分解。 [GPUMD 谱热流命令](https://gpumd.org/gpumd/input_parameters/compute_shc.html) · [Fan 等，2019](https://doi.org/10.1103/PhysRevB.99.064308)
