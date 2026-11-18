# MatterGen 入门

给定一组元素和一个性质目标时，搜索往往要先积累候选结构，再逐个评估。MatterGen 把一部分筛选条件放到生成阶段，让采样更偏向想找的结构。生成目录里的 CIF 是后续计算的输入，筛选的关键是追踪每个候选能否通过结构匹配、弛豫、稳定性和目标性质的检查。

## 一、把镜像从 WSL 带到 Linux 集群

下面是 WSL 构建 Docker 镜像、Linux 集群用 Apptainer 运行的环境记录。镜像 ID、容器名和路径需要替换为实际值。镜像标签由构建者指定，建议同时记录 `git rev-parse HEAD` 的输出和使用的检查点，便于后来定位代码与权重。

### 在 WSL 中准备容器

在 WSL 中启动 Ubuntu 容器：

```bash
docker run -it --user root --name mattergen-1.0.0 c42dedf797ba /bin/bash
```

进入容器后安装依赖：

```bash
apt update
apt install python3.10 python3.10-venv python3.10-dev
apt install python3-pip
apt install git-lfs
git lfs install
```

然后克隆 MatterGen 仓库到本地：

```bash
cd /opt/
git clone https://github.com/microsoft/mattergen.git
cd mattergen
```

使用 pip 和 uv 安装项目所需的环境依赖：

```bash
pip3 install uv
uv venv .venv --python 3.10
source .venv/bin/activate
export UV_HTTP_TIMEOUT=600
uv pip install -e .
```

使用 Git LFS 下载模型检查点：

```bash
git lfs pull -I checkpoints/
```

将容器内的环境路径写入启动配置：

```bash
echo 'export PATH="/opt/mattergen/.venv/bin:$PATH"' >> /etc/bash.bashrc
echo 'export VIRTUAL_ENV="/opt/mattergen/.venv"' >> /etc/bash.bashrc
```

### 在宿主机保存镜像并传到集群

回到管理该容器的 Docker 宿主机，生成镜像：

```bash
docker commit mattergen-1.0.0 mattergen:v1.0.0
docker save -o mattergen-1.0.0.tar mattergen:v1.0.0
```

将 `mattergen-1.0.0.tar` 上传至集群。构建时需要对归档文件有读取权限，共享时按使用范围授权。

通过 Apptainer 将其转换为 `.sif` 镜像：

```bash
module load apptainer
apptainer build --sandbox mattergen-sandbox docker-archive:///home/your-user/Software/mattergen/mattergen-1.0.0.tar
apptainer build mattergen.sif mattergen-sandbox
```

集群侧先进入镜像，再执行下面的生成命令。用 NVIDIA GPU 时，在实际分配了 GPU 的节点上启动容器，并选一个可写的输出目录。例如在镜像所在目录执行：

```bash
apptainer shell --nv mattergen.sif
```

## 二、先用基础模型确认输出，再引入性质条件

要从预训练的基础模型中采样，可以运行以下命令：

```bash
source /opt/mattergen/.venv/bin/activate
export MODEL_NAME=mattergen_base
export RESULTS_PATH=results/
mattergen-generate $RESULTS_PATH --pretrained-name=$MODEL_NAME --batch_size=16 --num_batches=1
```

这一批请求生成 16 个样本。跑通后检查输出目录的 `generated_crystals_cif.zip` 与 `generated_crystals.extxyz`，确认文件能读取，且结构数与采样设置相符。基础模型适合先排除运行环境、检查点加载和输出路径的问题。参见 [MatterGen 官方使用说明](https://github.com/microsoft/mattergen#generating-materials)。

### 用磁密度条件缩小候选范围

要生成具有特定属性的材料，可以使用微调模型。
例如，要从磁密度模型中采样，可以运行以下命令：

```bash
export MODEL_NAME=dft_mag_density
export RESULTS_PATH="results/$MODEL_NAME/"
mattergen-generate $RESULTS_PATH --pretrained-name=$MODEL_NAME --batch_size=16 --properties_to_condition_on="{'dft_mag_density': 0.15}" --diffusion_guidance_factor=2.0
```

条件值 `0.15` 是采样目标。比较引导系数时，固定检查点和采样数量，对照独立计算后有多少候选落入目标范围，同时检查不同结构占比。官方说明指出，加强引导往往能提高条件吻合度，也可能牺牲多样性。筛选时应记录两项结果。参见 [官方条件生成说明](https://github.com/microsoft/mattergen#property-conditioned-generation)。

## 三、从生成文件追到可复核的候选

以下命令沿用仓库记录中的 MP2020 参考数据路径。在 MatterGen 源码目录运行，确认 `RESULTS_PATH` 指向实际的生成结果。MatterSim 用于弛豫和估算能量，适合先处理整批候选。

```bash
git lfs pull -I data-release/alex-mp/reference_MP2020correction.gz --exclude=""
mattergen-evaluate --structures_path=$RESULTS_PATH --relax=True --structure_matcher='disordered' --save_as="$RESULTS_PATH/metrics.json"
```

评估结果写入 `metrics.json`。整体比例可以比较批次，挑选具体候选时还要把结构和逐项指标对回去。官方 CLI 提供 `--save_detailed_as` 保存逐结构指标，以及 `--structures_output_path` 保存弛豫结果。匹配器和参考库决定“新颖”的比较范围，能量修正与参考相图影响距凸包能。向同一表格汇总多批结果前，先对齐这些设置。参见[官方评估说明](https://github.com/microsoft/mattergen#evaluation)与[手册的晶体结构预测评价指标](../../晶体结构预测专题/评价指标与专业术语.md)。

手册[整理过 TaCr₂O₆ 案例](../../晶体结构预测专题/前沿成果、发展脉络与学习路径.md)。那里值得追的是生成的有序结构与实验无序晶体如何对应。生成后留下结构编号，记录弛豫是否改变了关键结构特征，再用相容的 DFT 计算复核目标候选、竞争相和目标性质。有实验对照时，说明计算模型怎样对应实际占位。把生成、计算筛选与实验对应的结果逐层留痕，才能解释某个候选为什么值得继续投入。

## 四、现成的条件模型什么时候需要微调

公开检查点已经支持目标属性时，可以先用它检查数据流和筛选口径。需要新的条件时，再看训练集是否包含足够的同口径标签，并留出独立结构验证目标能否被控制。下面保留基础模型训练和属性适配的命令入口。

```bash
mattergen-train data_module=mp_20 ~trainer.logger
```

要微调模型，可以使用以下命令：

```bash
export PROPERTY=dft_mag_density
mattergen-finetune adapter.pretrained_name=mattergen_base data_module=mp_20 +lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.$PROPERTY=$PROPERTY ~trainer.logger data_module.properties=["$PROPERTY"]
```

更换 `PROPERTY` 前，核对数据模块是否提供对应字段和单位，以及模型配置是否有可用的条件嵌入。先用公开检查点建立基线，再在相同生成预算和评估设置下比较微调结果。
