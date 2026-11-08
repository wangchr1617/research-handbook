# GPUMD 结构、扩散与离子电导

结构采样先用 RDF 判断邻近配位，动力学再看各组分的位移与速度相关。离子电导还包含组分间相关性，不能从单条 Li⁺ 自扩散曲线直接确定。

1. **RDF**：在平衡后的生产段用 `compute_rdf`，选择最大距离和分箱数，记录采样间隔。对均匀各向同性体相，第一极小值前的配位数由 $4\pi\rho_B\int_0^{r_{\min}}r^2g_{AB}(r)\mathrm dr$ 给出，$\rho_B$ 是被计数组分的数密度。薄膜、孔道和非均匀相需按几何解释归一化。
2. **自扩散**：用 `compute_msd` 检查按物种的展开位移，报告方向、单位和时间窗口。三维各向同性时 $D=\frac16\,\mathrm d(\mathrm{MSD})/\mathrm dt$。另用 `compute_sdc` 的速度相关积分检查时间窗和统计噪声。
3. **电导**：若版本提供 `compute_ic`，先按文档确认模型支持的电荷和组分定义。集体电流法依赖电荷流的相关函数。用 Nernst–Einstein 公式从各组分自扩散得到的值可作忽略交叉相关的对照。
4. **有限温度验证**：固定或测得实际密度后，延长轨迹并改变尺寸与种子。扩散慢时先检查实际跳跃事件、相态与 MSD 线性区，再拟合温度依赖。结构相变两侧分别报告，避免跨相拟合单一激活能。

参考 [GPUMD run.in 命令与单位入口](https://gpumd.org/gpumd/input_files/run_in.html)、[RDF](https://gpumd.org/gpumd/input_parameters/compute_rdf.html)、[MSD](https://gpumd.org/gpumd/input_parameters/compute_msd.html)及[自扩散](https://gpumd.org/gpumd/input_parameters/compute_sdc.html)。
