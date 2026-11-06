# VASP 并行参数设置

**适用环境：Linux（PBS 集群）；macOS / Linux（本机小测试）。**

先确认作业实际启动的 MPI 进程数，再选择并行参数。节点数、分配的 CPU 数、MPI 进程数和每进程 OpenMP 线程数不是同一个量；不要只把队列里申请的核数代入公式。

## KPAR 与 NCORE

对于普通单结构、纯 MPI 计算，且没有其他算法级分组时：

| 参数 | 含义 |
| --- | --- |
| `KPAR` | 将 MPI 进程分成多少组，各组处理不同 k 点 |
| `NCORE` | 同一条能带由多少个 MPI 进程协作 |
| `NPAR` | 能带并行组数，旧参数；现代版本通常优先设置 `NCORE` |

`KPAR` 应整除总 MPI 进程数；每个 k 点组内，`NCORE` 也应与可用进程数匹配。通常有：

$$N_{\mathrm{MPI}}=\mathrm{KPAR}\times\mathrm{NCORE}\times\mathrm{NPAR}.$$

例如启动 32 个 MPI 进程，`KPAR=4`、`NCORE=2`，每个 k 点组有 8 个进程，对应 4 个能带并行组。这里无需再写 `NPAR`。同时设置 `NPAR` 和 `NCORE` 时，旧参数 `NPAR` 优先，并不会自动按 `NCORE` 调整它。[官方 NCORE 说明](https://vasp.at/wiki/index.php/NCORE)解释了这一关系。

`KPAR` 使不可约 k 点均匀分配时通常更高效，但不要求它必须整除 `NKPTS`；整除 MPI 进程数才是分组约束。取值还受内存、通信和负载均衡影响，不能一概“设得越大越好”。参见 [KPAR 说明](https://vasp.at/wiki/index.php/KPAR)。

## PBS 与小测试

[单点案例的 job.pbs](../../../examples/vasp/minimal/single-point/job.pbs)从 PBS 节点文件取得进程数，设置 `OMP_NUM_THREADS=1`。先使用案例中的 `NCORE=1` 跑通流程，再在实际目标结构上比较少量合法组合。

比较时保持输入、电子精度及初始状态一致，查看：

```bash
rg 'NKPTS|NBANDS|LOOP:|LOOP\+' OUTCAR
```

重点比较相近电子步的耗时、总内存和完整作业时间，并核对能量与受力一致。第一步常有初始化开销；较大的 `NCORE` 还可能改变自动补齐的 `NBANDS`，因此不要只比较一行计时。

两原子示例能验证程序和提交方式，但不足以选择几十或上百核生产任务的最佳设置。性能测试应使用接近实际原子数、k 点数和能带数的任务。

## OpenMP、Gamma 与其他算法

混合 MPI/OpenMP 需要相应编译版本和正确的进程、线程绑定。线程数大于 1 时，VASP 不再按纯 MPI 的方式使用 `NCORE`；不要一边保留纯 MPI 的核数公式，一边额外增加线程。总进程数乘每进程线程数，应与分配的物理核资源匹配。设置方法见[官方混合并行说明](https://vasp.at/wiki/index.php/Combining_MPI_and_OpenMP)。

`vasp_gam` 仅用于单 Γ 点；多 k 点任务使用 `vasp_std`，不靠增加 `KPAR` 将 Gamma 版本变成多 k 点版本。GPU、NEB 的 `IMAGES` 分组和部分响应算法也有各自的并行约束，应结合版本与对应任务说明设置。
