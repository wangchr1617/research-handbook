# Hefei-NAMD 安装与首个公开算例

先跑作者提供的 MoS₂/WS₂ 公开练习，确认 Fortran 可执行文件能读入配套的能级与非绝热耦合，再自行生成逐帧 VASP 波函数。这样能分别定位编译、输入和波函数读取问题。下文沿用作者 2021 年公开教程所用的 `src/namd` 接口。

## 一、编译并确认调用的是哪个 namd

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

## 二、用 MoS₂/WS₂ 的文本耦合跑通传播

在新目录放入作者同一练习的 `inp`、`INICON`、`EIGTXT` 和 `NATXT`。作者所用版本在 `LCPEXT=.TRUE.` 且目录中存在 `COUPCAR` 时读取两份文本。这个模式下 `COUPCAR` 可以是空文件。若日志开始查找 `WAVECAR`，先检查运行目录及上述条件，再对照当前版本的读入逻辑。

练习的带窗为 325 至 335，共 11 条带。第一条初始条件是从第 1 帧的第 329 带出发。 `NSW=2000` 给出输入轨迹范围，`NAMDTIME=1000` 与 `POTIM=1 fs` 对应约 1 ps 的单次传播。按这版教程，逐行检查起点加 `NAMDTIME` 严格小于 `NSW`，同时核对起始带在窗内、`INICON` 行数与 `NSAMPLE=100` 一致。

在输入目录运行 `/实际路径/Hefei-NAMD/src/namd/namd > namd.log 2>&1`。先在日志确认读入方式，再检查 `PSICT.*` 的展开系数和 `SHPROP.*` 的带布居，文件名后缀对应初始条件中的起点。后处理按相对传播时间对齐各起点，核对初态占据和传播窗。要看电子是否换层，可接着读[界面转移与布居读图](Hefei-NAMD界面转移与布居读图.md)。

公开下载、输入字段与文件格式见[作者教程](https://qijingzheng.github.io/posts/Hefei-NAMD-Training/)及[上游训练目录](https://github.com/QijingZheng/Hefei-NAMD/tree/master/doc/training_2020)。从自建晶胞开始的步骤见[载流子弛豫](Hefei-NAMD载流子弛豫.md)。
