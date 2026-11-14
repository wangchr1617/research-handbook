# CP2K 偶极轨迹与红外光谱

正常模分析提供势能面极小点附近的简谐频率。若要观察液体中振动带的展宽和随温度变化的谱形，可沿 AIMD 轨迹计算偶极或极化，再对时间关联函数做频谱分析。速度自相关适合看振动态密度。红外强度还取决于振动引起的偶极变化。

## 选择偶极的定义

| 模型 | 取量与检查 |
| --- | --- |
| 孤立中性分子 | 用 `FORCE_EVAL/DFT/PRINT/MOMENTS` 输出偶极，保持坐标参考和采样间隔一致。带电体系还需说明坐标原点及整体运动 |
| 周期绝缘体 | 通过 Berry 相位极化追踪连续分支，或用局域化的 Wannier 中心和离子芯电荷计算偶极。跨周期边界时按同一分子重组坐标与中心，核对每帧中心数及归属 |
| 分子片段与溶剂 | 片段自相关用于分解贡献。总体系谱还包含片段间交叉相关，比较时保存所用的偶极定义 |

对闭壳层局域化表示，每个双占据 Wannier 中心贡献 $-2e\mathbf r_i$。离子项使用与赝势相容的芯电荷。可在 `DFT/LOCALIZE/PRINT/WANNIER_CENTERS` 用 `IONS+CENTERS` 同时输出离子和中心，用 `EACH/MD` 控制采样。后处理前核对结构、中心文件和能量文件时间步一致。用 TRAVIS 时，输入实际晶胞和帧间物理时间，保存交互设置与导出的频谱。语法以 [CP2K 输入手册](https://manual.cp2k.org/)与 [TRAVIS](https://www.travis-analyzer.de/)为准。

将下面两段放入 `FORCE_EVAL/DFT`，可用[单水分子的短 AIMD 案例](../../../examples/cp2k/minimal/molecular-dynamics/README.md)核对文件交接。已有同名 `PRINT` 或 `LOCALIZE` 节时，合并对应的子节。

```text
&PRINT
  &MOMENTS ON
    &EACH
      MD 1
    &END EACH
  &END MOMENTS
&END PRINT
&LOCALIZE
  METHOD CRAZY
  &PRINT
    &WANNIER_CENTERS ON
      IONS+CENTERS
      &EACH
        MD 1
      &END EACH
    &END WANNIER_CENTERS
  &END PRINT
&END LOCALIZE
```

在 CP2K 2026.2 的六步水分子试算中，初始结构加六个 MD 步各输出一次偶极及中心坐标。默认文件名含 `HOMO_centers`。分析前按数值步号排列文件，并核对每帧有 3 个原子与 4 个双占据中心。这段短轨迹用于验证数据输出，计算可分辨的光谱还需要更长的平衡生产轨迹。

### 在 Alkemie 中采集分子偶极

对孤立中性分子，可使用「分子优化 → AIMD 偶极轨迹」模板。动力学节点从优化的 restart 读取坐标与晶胞，用 `PERIODIC FALSE` 的分子偶极算符把逐步结果写入 `dipole.moments`。同时保留 `alkemie-1.ener` 和 `trajectory.extxyz`，可用能量文件第一、二列的步号和时间（fs）与偶极帧配对。步号从 0 开始，运行 6 步应有 7 帧。结果页显示三个笛卡尔分量（D），完整时间序列以原始文件为准。已准备好结构时，可直接连接偶极轨迹组件。

## 从时间序列到可比较的谱

1. 选平衡后的等时间间隔片段，先画偶极三个分量。周期 Berry 相位的分支跳变会产生宽带伪信号，先处理分支并核对轨迹。
2. 若输出间隔为 $\Delta t$，可解析频率上限为 $1/(2\Delta t)$。相关时窗为 $T_{\mathrm{corr}}$ 时，典型频率间隔约为 $1/T_{\mathrm{corr}}$。例如每 2 fs 采一帧，上限约为 $8340\ \mathrm{cm^{-1}}$。零填充可加密绘图网格，实际分辨率仍由有效时窗决定。
3. 由去均值偶极的自相关得到功率谱。转换成吸收强度时，记录所用的频率因子、温度和量子修正。比较峰位可用归一化谱，比较强度还要对齐体积、采样、归一化和仪器条件。
4. 用多个相关窗口、分块与独立轨迹检查峰位和展宽。CP2K 的静态 Raman 或红外正常模与 AIMD 红外谱采用不同的物理量，Raman 谱需要极化率涨落。

参考 [CP2K 光谱教程](https://www.cp2k.org/_media/events:2015_cecam_tutorial:iannuzzi_spectroscopy_b.pdf)、[CP2K AIMD 练习](https://www.cp2k.org/exercises:2015_pitt:aimd)和[CP2K 振动频率](CP2K振动频率.md)。
