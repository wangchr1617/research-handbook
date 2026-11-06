# OVITO 安装与基础操作

**适用环境：Windows、macOS、Linux；图形操作在有桌面的本机完成。**

OVITO 用于查看原子结构、轨迹和分析结果。先把文件类型、晶胞和粒子属性看对，再添加分析操作。

## 一、下载与安装

打开 [OVITO 官网](https://ovito.org/)，从 Download 选择自己的系统和芯片版本。当前支持范围以 [官方安装说明](https://www.ovito.org/manual/installation.html)为准，旧 Intel Mac 或旧 Linux 不一定能使用最新包。

Windows 运行安装程序；Mac 打开安装包并放入“应用程序”；Linux 解压到个人目录，按包内说明启动 `bin/ovito`。初学者先用 Basic 查看结构与常用修改器，Pro 的附加功能按官网许可说明选择。

图形应用和 Python 模块是不同使用方式。安装 Basic 不等于当前 Conda 环境已经能 `import ovito`；Python 批处理另见 [OVITO Python](OVITOPython批量分析.md)。无需为了第一次打开结构就先配置 Docker。

## 二、用一个小文件认识界面

将下面内容保存为 `two-atoms.dump`，文件名不要带 `.txt` 后缀：

```text
ITEM: TIMESTEP
0
ITEM: NUMBER OF ATOMS
2
ITEM: BOX BOUNDS pp pp pp
0 10
0 10
0 10
ITEM: ATOMS id type x y z
1 1 2 5 5
2 2 4 5 5
```

这是边长 10、两粒子间距 2 的人工演示，长度单位假设为 Å，不是实际 GeTe 晶体。它采用 LAMMPS dump 格式，`id` 是身份编号，`type` 是类型编号，`x y z` 是坐标。

1. 在 OVITO 用 `File → Load File` 载入文件，确认识别出两个粒子。
2. 查看 Simulation cell，确认三个方向边长都是 10，周期边界与 `pp pp pp` 一致。
3. 在粒子类型设置中为 type 1、2 修改显示名称和颜色。显示映射不等于模拟输入中的元素定义或势函数，定量分析仍需核对属性和单位。
4. 旋转、平移与缩放视图，检查两粒子的位置关系，再尝试添加 Coordination analysis，cutoff 设为 `2.5`。
5. 在粒子属性表查看 Coordination；两个粒子的配位数都应为 `1`。

## 三、数据管线是什么

Source 是原始输入，每添加一个 modifier，就对前一步的数据做处理。选择粒子、删除选中粒子、结构分析的先后顺序会改变分析对象。

例如想统计完整体系的 RDF，应先做 Coordination analysis，再为了展示隐藏部分粒子；先真正删除一半粒子再算 RDF，计算的就是删减后的体系。关闭一个修改器可比较处理前后，原始输入文件不会因此被覆盖。

## 四、轨迹与导出

载入多帧轨迹后，用时间滑块切换帧。帧序号、模拟步数和物理时间不是同一个量，物理时间需要结合输出间隔和时间步长换算。

用保存会话功能保存管线和显示设置（通常为 `.ovito`），数据文件路径仍需可访问。导出数值数据与渲染图片是两类操作：前者保存分析结果，后者保存视图。截图漂亮不代表分析参数正确。

分享结果时同时记录输入来源、软件版本、修改器顺序、cutoff 和单位。配位数与 RDF 的完整例子见 [配位分析](配位数与径向分布函数.md)，点缺陷见 [Wigner-Seitz](Wigner-Seitz缺陷分析.md)。
