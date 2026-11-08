# Hefei-NAMD 安装与首个公开算例

先跑作者提供的 MoS₂/WS₂ 公开练习，确认 Fortran 可执行文件能读入配套的能级与非绝热耦合，再自行生成逐帧 VASP 波函数。这样能分别定位编译、输入和波函数读取问题。下文沿用作者 2021 年公开教程所用的 `src/namd` 接口。

## 编译并记录版本

在有 Fortran 编译器与 `make` 的 Linux 环境中准备源码。实际构建前先检查该提交的 Makefile 以及编译器设置。

```bash
git clone https://github.com/QijingZheng/Hefei-NAMD.git
cd Hefei-NAMD
git rev-parse HEAD
cd src/namd
make
test -x namd
```

记下提交号、编译器版本和可执行文件的完整路径。`namd` 是通用名称，直接调用刚编好的可执行文件可避免误用同名程序。

## 第一次从预计算耦合运行

1. 从作者页面取得同一公开练习的输入和能级/耦合数据。在独立目录保留 `inp`、`INICON` 及其匹配的 `EIGTXT`、`NATXT`。使用文本耦合模式时，按作者对该版 `LCPEXT` 和 `COUPCAR` 的说明准备文件。
2. 核对 `BMIN/BMAX` 的带窗口、`NSW` 的帧数、`POTIM` 的帧间隔，以及 `NSAMPLE` 与 `INICON` 行数。`INICON` 的初始带要位于窗口内，起始帧与传播时长之和要小于数据覆盖帧数。
3. 在包含输入文件的目录运行 `/实际路径/Hefei-NAMD/src/namd/namd > namd.log 2>&1`。检查标准输出确认读取的数据来源和初态，再核对能级、布居输出的时间轴与带范围。
4. 后续使用自算 `WAVECAR` 时，在新目录运行。改变轨迹、选带或采样间隔后重新生成耦合或证明缓存完全匹配。

公开下载、输入字段与文件格式见[作者教程](https://qijingzheng.github.io/posts/Hefei-NAMD-Training/)及[上游训练目录](https://github.com/QijingZheng/Hefei-NAMD/tree/master/doc/training_2020)。从自建晶胞开始的步骤见[载流子弛豫](Hefei-NAMD载流子弛豫.md)。
