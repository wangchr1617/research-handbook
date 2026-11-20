# Docker 与 Kubernetes 企业迁移部署

把一套在虚拟机或 Compose 上运行的业务迁到新环境，需要处理镜像、运行平台、业务数据和流量入口。先定下恢复时间目标（RTO，即允许中断多久）和恢复点目标（RPO，即最多允许丢失多长时间内写入的数据），再据此选择平台和切换方式。Dockerfile、Compose 和日志排查可先读[Docker 与 Linux 运维](Docker与Linux运维.md)。

## 一、先按业务和团队条件选运行平台

Docker 可把应用和运行依赖做成标准容器镜像，镜像经仓库分发。Kubernetes（K8s）负责在多节点上调度容器、维持副本和服务发现。节点通过容器运行时接口（CRI）使用 containerd 或 CRI-O 等运行时，同样可以运行 Docker 构建的兼容镜像。可在 CI 中构建镜像，并用同一镜像摘要部署预发和生产，把环境差异留给配置。在 ARM 开发机上构建时，要确认镜像支持生产节点的架构，例如 `linux/amd64`。 [Kubernetes 容器运行时](https://kubernetes.io/docs/setup/production-environment/container-runtimes/) · [镜像摘要](https://kubernetes.io/docs/concepts/containers/images/) · [Docker 多架构构建](https://docs.docker.com/build/building/multi-platform/)

| 目标平台 | 适用条件 | 迁移时要接手的工作 |
| --- | --- | --- |
| 虚拟机上的 Docker Compose | 服务少，小团队发布，业务允许宿主机故障时由运维恢复 | CI 推送镜像，生产主机按 Compose 配置拉取并重建服务。另设 HTTPS 入口、日志、备份及恢复流程。单台宿主机仍是故障点。 |
| 云托管容器服务，例如 ECS 配合 Fargate | 团队想把镜像交给云平台运行，接受平台的服务定义和集成方式 | 把 Compose 服务改成平台的任务与服务，接入云负载均衡、私网、身份和日志。后续换平台时需转换这部分配置。 |
| 托管 Kubernetes，例如 EKS、AKS、GKE | 多个服务或团队要共用 Kubernetes API、网络入口和发布流程，希望由云厂商运维控制面 | 团队仍要维护业务工作负载和数据，并按托管模式确认节点、网络、存储和升级的责任边界。 |
| 自管 Kubernetes | 本地机房、隔离网络，或需要自定义节点、网络及存储 | 平台团队负责控制面高可用、etcd 备份、证书和升级，还要提供镜像仓库、入口和存储驱动。离线环境需让节点能从内网仓库拉取业务镜像及集群组件镜像。 |

已有 Docker Swarm 的团队也可以沿用 Swarm 服务和集群调度。`docker stack deploy` 采用旧版 Compose v3 文件格式，迁移现有 Compose 项目时要检查所用字段的兼容性。 [Docker Compose 生产部署](https://docs.docker.com/compose/how-tos/production/) · [Docker Swarm Stack](https://docs.docker.com/engine/swarm/stack-deploy/) · [AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) · [Kubernetes 生产环境](https://kubernetes.io/docs/setup/production-environment/)

## 二、把 Compose 职责映射到目标环境

先用依赖图或台账列出域名、进程、数据目录、端口、访问凭证、计划任务和上下游。传统虚拟机应用可以先把现有进程容器化，保留原有数据库与外部接口，再迁入集群。已有 Compose 项目时，可复用镜像、启动命令和环境变量约定，按每个服务的职责编写 Kubernetes 资源。`kompose convert` 可以生成初稿，生产前还需复核流量入口、探针、权限和存储。 [Kubernetes 的 Compose 转换指南](https://kubernetes.io/docs/tasks/configure-pod-container/translate-compose-kubernetes/)

| Compose 或虚拟机上的职责 | Kubernetes 中的常见做法 | 迁移要检查的细节 |
| --- | --- | --- |
| Web API、常驻队列 worker | 分别用 `Deployment` 管理。API 前加 `Service`，主动消费队列的 worker 通常无需入站 `Service` | 两类进程独立设置副本和 CPU、内存 `requests`。API 就绪后再接流量，worker 终止时按队列语义完成或重新投递任务。 |
| 反向代理、对外端口和域名 | `Service` 提供稳定的集群内入口，对外由支持的 Gateway API 或 Ingress 实现接入 | 验证 TLS、转发头、超时和长连接。整个迁移期间跨机房或跨集群的分流，通常由能同时访问新旧环境的上游负载均衡实现。 |
| `.env`、挂载配置、应用身份 | 用 `ConfigMap` 管理非敏感配置，凭证可用 `Secret` 或外部密钥服务，工作负载用各自的 `ServiceAccount` | 限制凭证读取权限，确认加密与轮换方式。`Secret` 中的 Base64 编码只用于表示数据。 |
| `healthcheck` 和 `depends_on` | 按职责设置 `startupProbe`、`readinessProbe`、`livenessProbe`，由应用处理依赖重连 | 启动探针为慢启动预留时间。就绪探针控制接流量，存活探针用于发现需要重启的容器。把数据库连通性放进存活探针，数据库波动时可能触发 API 实例集体重启。 |
| 定时任务、建表或升级脚本 | `CronJob` 运行定时任务，独立 `Job` 执行该次发布所需的数据库变更 | 源端和目标端交接定时任务。数据变更脚本要能安全重试，由发布流程控制执行时机。 |
| 数据库、命名卷、本地上传目录 | 数据库可先留在原处或用托管实例。确需在集群内运行时，可用 `StatefulSet` 和持久卷，并独立安排主从、备份与恢复 | `PersistentVolumeClaim`（PVC）申请存储，旧数据需另行迁入。确认容量、访问模式、可用区和恢复速度。会被多个实例读取的上传文件通常放共享存储或对象存储。 |

若原系统依赖宿主机上的授权文件、固定 IP 或特定硬件，也要检查目标环境是否能提供同等能力。需要抵御单节点故障时，要让副本分散到不同节点，并留出故障后重调度所需的容量。在预发可模拟某个节点上的实例退出，检查新实例是否能继续读取用户会话、上传文件和任务状态。 [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) · [Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/) · [探针](https://kubernetes.io/docs/concepts/workloads/pods/probes/) · [Secret 管理](https://kubernetes.io/docs/concepts/security/secrets-good-practices/) · [持久卷](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

## 三、带附件的任务怎样试迁移

用仓库的 Agent Demo 作为迁移验收起点。它用 Compose 启动 API、Celery worker、dispatcher、Redis 和 PostgreSQL。先在源端提交一条含文本附件的任务，记录 `run_id`、附件标识、终态与最后一个事件 ID，切到目标环境后用同一账号和原 ID 核对记录。Demo 的小附件内容随数据库恢复。实际应用若使用对象存储，还需核对文件版本和授权。以下步骤是迁移方案（参考 [Demo 请求与恢复实操](../../../examples/backend/agent-demo/请求与恢复实操.md)）：可以先让新集群上的 API 接入原有数据库、队列和共享文件存储，等应用稳定后再另开窗口迁数据库。切换步骤可按以下顺序安排。

1. **部署并验收新入口。** 先用预发数据演练恢复，再用独立测试入口验证登录、权限、上传、投递小任务和 SSE 断线重连。确认新旧 API 都能读写当前表结构和任务格式。如果原来把文件放在 Compose 本地卷，先完成共享存储切换并验证源、目标两端访问的是同一份文件。
2. **先试 API 流量，再交接消费者。** 原 worker 先继续消费原队列，新 API 投递格式保持兼容。少量流量进入新 API 后，按版本看 HTTP 错误率和延迟，同时观察共享队列的积压、任务成功率和状态一致性。在事先约定的观察窗口内满足验收阈值后再放量。切 worker 时，从旧端停止领取新任务并检查在途任务，按队列确认与重投机制启动新端，验证重复投递能按任务 ID 幂等处理。交接定时任务时，先停旧调度器，再启用新调度器。
3. **应用稳定后再迁数据。** 数据量小且有维护窗口时，可以停写后备份、恢复并检查目标。窗口较短时可先做全量和增量同步，再暂停源端写入，等目标追到最后提交，核对关键记录和业务查询后开放写入。例如 PostgreSQL 原生逻辑复制会复制表行，库结构变更和序列值需要另外同步，启用目标库写入前要检查。 [PostgreSQL 逻辑复制限制](https://www.postgresql.org/docs/current/logical-replication-restrictions.html)
4. **按实际写入位置决定怎么退。** 两端应用共用同一数据库且版本兼容时，可以先把入口切回旧应用，并按同样的交接流程处理 worker。目标库开始独立接收写入后，旧库会缺少这些变更。要切回旧库，需先处理这些新增数据，例如按演练过的方案反向同步并校验。应用可先保留向前、向后兼容的表结构，等回退窗口结束再删除旧字段。

恢复演练要计时，并检查最后一笔可恢复的业务写入，再对照 RTO 和 RPO。先核对开头那条历史任务的附件和事件，再在测试环境提交新任务确认 worker 能领取、结果能写回。如果迁移窗口还有未处理任务，检查的是原 run 是否继续推进，以及最终是否只有一份成功结果。 [队列恢复的检查方法](../并发与任务/后台任务队列与恢复.md)

## 四、按新旧两端能否共存选择切流方式

**发布产物。** CI 测试应用、构建镜像并推送到仓库，记录代码提交与镜像摘要。简单服务可在流水线中用 `kubectl apply` 或 `helm upgrade` 发布。多环境可以用 Helm chart 配置参数，或用 Kustomize 在一份基础清单上叠加环境差异。采用 GitOps 时，流水线提交目标镜像和配置，由 Argo CD 或 Flux 在集群侧同步。回退时应恢复 Git 中的期望状态，并确认控制器已同步到对应版本。 [Helm chart](https://helm.sh/docs/topics/charts/) · [Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/) · [Argo CD 同步策略](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) · [Flux 工作方式](https://fluxcd.io/flux/concepts/)

| 切换方式 | 适用条件 | 切换与恢复 |
| --- | --- | --- |
| 滚动更新 | 同集群内更新应用，新旧版本能短期并存 | `Deployment` 按 `maxSurge` 和 `maxUnavailable` 逐批替换 Pod，结合就绪探针控制接流量。保留可恢复的旧版本。 |
| 蓝绿切换 | 能同时运行两套环境，需要先整体验证目标，再切换入口 | 先通过独立入口验收新环境，再切换上游路由。旧环境可保留一段时间，切回前要确认它能读取切换后写入的数据。 |
| 金丝雀发布（灰度） | 能分流并分别观测两侧，希望逐步放量 | 用支持分流的网关或负载均衡控制请求比例，按错误率、延迟和业务结果决定是否继续。需要自动化时，可用 Argo Rollouts 配合兼容的流量路由。 |
| 计划停机切换 | 源端与目标端无法安全并行写入，业务允许维护窗口 | 停止写入和定时任务，排空或交接队列，完成最后同步和核验，再开放目标端写入。停机窗口按恢复演练耗时估算。 |

灰度比例由路由决定。Pod 副本数可以影响流量分布，但实际请求还受连接复用、会话粘滞和长连接影响。回滚前分别确认流量、应用和数据的状态。`kubectl rollout undo` 恢复的是 `Deployment` 的 Pod 模板版本，数据库结构、队列和外部配置要按各自的恢复方案处理。 [Deployment 更新和回滚](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) · [Gateway API 流量分配](https://gateway-api.sigs.k8s.io/guides/user-guides/traffic-splitting/) · [Argo Rollouts 流量管理](https://argo-rollouts.readthedocs.io/en/stable/features/traffic-management/)

## 五、换集群后怎样验收依赖和数据

先在目标集群核对 API 版本、自定义资源定义（CRD）及其控制器、存储类、入口、服务身份和外部依赖，再用 Git 中的清单重建应用。已有的 Kubernetes 对象和卷数据也可按需用 Velero 备份恢复。跨云迁卷时，应按目标存储选择可用的复制方式，原云存储的快照可能无法直接使用。数据库仍需单独演练恢复，核对业务数据的一致性，并在切流时明确由哪一端接收写入。 [Velero 跨集群迁移](https://velero.io/docs/main/migration-case/)
