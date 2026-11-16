# DeerFlow 智能体框架与 Archeos

给模型一份预测结果，请它计算误差并交付一份可复核的报告。模型需要决定读哪个文件、调用什么工具、如何解释结果。DeerFlow 把模型的工具调用变成实际操作，管理对话状态和工作文件。Archeos 用它运行智能体，由自己的工作台和科研服务处理成员授权、计算执行、结果验收与交付。

本文讲 DeerFlow 2.x 的架构。DeerFlow 1.x 以 Deep Research 流程为主，2.0 重构为支持工具、技能、沙箱和子智能体的通用运行框架（agent harness）。Archeos 部分以本地检出的 `e412ba0` 为准。该提交的 `upstream.lock.json` 记录 DeerFlow 基线 `2a9e7255a7c9bb50b8d0bb5b5b5028095f2ad94d`（`2.3.0-dev`）和 Extension API `0.2.11`。阅读 Archeos 源码链接需要相应的仓库权限。[DeerFlow 2.0 发布说明](https://github.com/bytedance/deer-flow/discussions/3795) · [Archeos 引擎锁定清单](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/upstream.lock.json)

## DeerFlow 怎样跑一轮

在上游项目中，Gateway 接收线程和运行请求，并提供 SSE 流式接口。后端的 `make_lead_agent()` 组装主智能体，使用 LangChain 接入模型、工具和中间件，使用 LangGraph 管理运行状态。模型收到消息和可用工具的描述，生成工具调用。框架执行允许的调用，把结果送回模型，模型再根据结果决定继续调用还是回答。中间件在模型或工具调用前后处理附件、上下文、预算等横切逻辑。[DeerFlow 系统架构](https://github.com/bytedance/deer-flow/blob/main/docs/ARCHITECTURE.md) · [DeerFlow 后端架构](https://github.com/bytedance/deer-flow/blob/main/backend/docs/ARCHITECTURE.md)

| 组件 | 在一次任务中的职责 |
| --- | --- |
| 工具与 MCP | 工具是模型可请求的一次操作，如读取文件、查询或展示产物。MCP 是把外部服务的工具接入运行框架的一种协议。工具的可用范围和调用身份由运行时与服务端检查。 |
| 技能（Skill） | 用 `SKILL.md` 描述某类任务的工作步骤、检查方法及配套资源。比如先核对两列数据的单位，再计算 RMSE。框架加载技能说明，实际读文件和运行计算仍由已授权的工具完成。 |
| 子智能体 | 主智能体可以把相对独立的工作委派给子智能体，各自处理分配到的上下文，再汇总结果。例如两组文献各自查证，主智能体负责比较条件和引用。 |
| 沙箱 | 为文件和命令工具提供执行环境。会话的上传、工作和输出目录各有用途。目录作用域、容器及网络隔离取决于实际启用的提供方和配置。 |
| 检查点、摘要和记忆 | 检查点按线程记录图状态。摘要压缩送给模型的上下文。启用长期记忆时，选取的事实或偏好可用于后续对话。原始数据、计算结果和校验记录应保存在有独立标识的文件或业务记录中。 |

读源码时可先找 `make_lead_agent()`，再看它怎样收集可用工具和加载技能。用“读取一份附件”追踪一轮，观察文件引用怎样进入模型上下文，工具返回的数据怎样进入下一次调用。长文档可让工具读取相关片段，原件继续保留在文件中。[DeerFlow 核心概念](https://github.com/bytedance/deer-flow/blob/main/frontend/src/content/en/introduction/core-concepts.mdx) · [LangGraph 检查点](https://docs.langchain.com/oss/python/langgraph/persistence)

## Archeos 怎样接入这一轮

Archeos 在 `vendor/deer-flow/` 维护带锁定清单的 DeerFlow 后端，并为团队运行独立引擎实例。浏览器访问 Archeos 自己的工作台。平台校验登录会话、团队成员和对应业务资源的访问权限，再由服务端 HTTP 适配器把请求送给团队引擎，传递平台核定的成员身份。模型循环、消息和检查点由引擎管理。Archeos 的领域能力通过扩展契约、工具服务和业务 API 接入。例如 Scientific Compute 的 DeerFlow 适配器注册计算服务，并将授权的成员、线程和文件作用域绑定到计算工具上下文。[Archeos 开发说明](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/development.md) · [工作台代理](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/backend/archeos/engine/workbench.py) · [DeerFlow HTTP 适配器](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/backend/archeos/engine/deerflow.py) · [科学计算扩展](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/packages/scientific-compute/scientific_compute/adapters/deerflow.py)

| 想确认什么 | 查看哪里 |
| --- | --- |
| 这里调用的是哪条会话 | `thread_id` 定位线程，按当前身份核对线程和项目的访问授权。 |
| 浏览器刷新后显示的是哪一轮 | `run_id` 定位已有引擎运行。重连用 GET 订阅同一轮的流，携带 `Last-Event-ID` 标明上次收到的事件。 |
| 计算是否结束，结果是否已交付 | 查计算服务的作业标识、退出码、数值验收和文件回执。模型运行结束时，独立作业可能仍在等待或执行。 |

需要等待长作业时，Archeos 在启用自动续接且登记成功的场景下，可根据持久作业回执和完成事件派发后续一轮。派发前复查成员、线程授权和取消状态。此时新的引擎运行接手已有作业结果，与浏览器重连原运行是两条路径。已配置的聊天沙箱和科学计算执行环境也应分别核对，后者按部署的执行策略决定允许的计算位置。[Archeos 对话运行](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/conversation-runtime.md) · [计算任务与续接](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/compute-runs.md)

## 用 RMSE 小案例对照结果

可用手册的 [RMSE 小案例](../../../examples/rmse/README.md)做基准。数据是人工构造的三行样本，两列单位均为 `eV/atom`，误差为 `+1`、`-1`、`+1`，预期 RMSE 为 `1.000000 eV/atom`。本地可在手册根目录运行 `python3 examples/rmse/run.py` 核对。

在已配置模型、Scientific Compute 和执行环境的 Archeos 中，可上传 [data.csv](../../../examples/rmse/data.csv)，用下面的请求观察一轮操作。

> 用附件的 `reference` 和 `prediction` 两列计算 RMSE，单位均为 `eV/atom`。先检查列名和样本数，保留原 CSV，生成包含样本数、RMSE 和单位的 `values.json`。使用已配置的 Python 分析工具，按样本数为 3、RMSE 与 1 的绝对差不超过 `1e-6 eV/atom` 验收，并交付结果文件。若工具或验收不可用，请说明发生在哪一步。

在这个练习里，DeerFlow 负责读入附件引用、运行模型与工具循环并返回流式事件。Archeos 的 Scientific Compute 可以用 `compute_run_python` 执行分析，把 `scientific_checks` 随任务固定下来，再从实际输出独立检查数值与单位。验收时查看三处记录：进程是否正常退出、JSON 中的字段是否满足已声明条件、交付文件能否对应到该次运行。若程序返回零退出码，且写出了样本数为 2 的 JSON，进程状态仍可正常，数值验收应失败。真实势模型的误差判据还需要参考集、数据划分和单位依据，本例的阈值只用于固定的教学数据。[Archeos 数值验收与交付](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/compute-runs.md)

授权与流式请求可对照[Archeos 与 ALKEMIE 源码阅读](Archeos与ALKEMIE源码阅读.md)。要追溯文献证据如何进入回答，可读[Archeos 与 Alkemie 的知识链路](../../知识工程/Archeos与Alkemie的知识链路.md)。
