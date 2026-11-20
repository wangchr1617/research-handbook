# DeePMD-kit 安装

接手旧的 `graph.pb` 模型时，先确定需要的是 CPU 上核对预测、GPU 训练，还是给已有的 LAMMPS 加载模型。这三种用途的验收不同。下面沿用 Linux x86_64 上 DeePMD-kit 2.2.7 的离线安装场景，迁移时以模型的版本和后端为起点，详细步骤可参考 [2.2.7 安装文档](https://docs.deepmodeling.com/projects/deepmd/en/v2.2.7/install/easy-install.html)。

## 一、离线节点先把模型评估跑通

从[发布页](https://github.com/deepmodeling/deepmd-kit/releases/tag/v2.2.7)选对应架构和设备的安装包。CPU 版可用于在少量构型上核对能量和力。若要用 CUDA，按发布说明选择 GPU 版，并核对目标节点驱动。发布资产若分成多段，按文档给定的顺序拼接后再运行。在保存安装包的目录执行，激活命令里的路径改为安装器实际使用的前缀。

```bash
bash deepmd-kit-2.2.7-cpu-Linux-x86_64.sh
conda activate /path/to/deepmd-kit
command -v dp
dp --version
```

安装器询问是否改写 shell 初始化时，可选 `no`，之后从已能使用 Conda 的 shell 激活该前缀。先用[入门笔记中的模型评估](DeePMD入门.md#导出模型并检查预测)在少量有参考标签的构型上对照，再把模型交给 LAMMPS。

## 二、到目标节点核对 LAMMPS 和 GPU

若使用配套的 LAMMPS，先确认激活环境内的 `lmp -help` 能列出 `deepmd`。若接入外部 LAMMPS，则按所选版本核对插件加载方式和二进制兼容性。先在同一结构上做零步能量、逐原子力对照，再用相同原子数、步数和输出频率比较速度。

原集群记录中使用了 CUDA 11.7 和 Intel MPI。迁移时在实际计算节点运行 `nvidia-smi`，核对分配到的 GPU 和驱动。输出右上角的 CUDA 版本反映驱动支持能力，若需编译还要用 `nvcc --version` 查看工具链。多进程执行时，用与 LAMMPS 构建匹配的 MPI，先通过单进程测试再增加进程。若走容器路线，从发布文档选择固定标签，并在节点上复做相同的模型和插件检查。
