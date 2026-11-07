# Archeos 与 Alkemie 的知识链路

本篇按 2026-11-07 核对的源码阅读知识处理流程：Archeos 提交 `275ee9c5edcf4df6c773512d8576cb0010168fd4`，Alkemie 提交 `f3b7481df6920ab14c30a01e7a48dd565130d430`。下面描述代码职责；部署是否启用模型、解析服务和索引，需要在对应环境另行检查。

## Archeos：从上传文档到可引用证据

相关代码集中在 `backend/extension/mineru`，平台入口位于 `backend/archeos/engine/knowledge_tools.py`。目录以 MinerU 命名，但还包含任务、索引、检索和回答处理，阅读时需区分上游解析器与项目自身逻辑。

| 源码入口 | 关注的职责 |
| --- | --- |
| [client.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/client.py) | 上传文件、创建解析任务、轮询、限量下载 |
| [local_service.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/local_service.py) | 独立 MinerU 4.x 环境及本机服务启动 |
| [worker.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/worker.py) | 持久任务、恢复、任务代次与结果接收 |
| [parsing.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/parsing.py) | 结构内容提取、页码、块定位、切块 |
| [retrieval.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/retrieval.py) | 授权范围、词法与稠密检索、排名融合 |
| [knowledge_tools.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/engine/knowledge_tools.py) | 成员、线程、活动运行及工具回调校验 |

先沿 `MinerUClient.submit → poll → download` 阅读服务边界。上传返回地址必须与配置服务同源；结果下载有大小限制。`worker.py` 用 `owned_job` 检查任务仍处于处理状态且代次一致，防止重试或删除后接收旧结果。

`parsing.chunks` 优先读取结构化页块，把 `page_idx` 转成从 1 开始的物理页码；缺少结构时按 Markdown 段落回退。长文本按步长 1600 字符取最多 1800 字符片段，形成最多 200 字符的相邻重叠。它是字符切块，不能据此推算固定 token 数，也不能保证表格语义完整。

进入 `retrieval.current_scope` 后，候选片段受文库、解析完成状态、索引状态和来源版本共同约束。`authorize_entries` 对显式文档范围进行校验，文档不就绪时返回索引待处理错误；这样调用方不会因指定资料暂不可用而悄悄搜索更大范围。

最后看 `knowledge_tools.caller` 与 `active_run`：内部令牌、有效成员、线程授权与活动运行一起约束工具回调。回答引用可以持久保存，工具执行权限则随当前成员和运行状态重新检查。可结合[用户认证与 Agent 安全](../后端工程/接口与安全/用户认证权限与Agent安全.md)理解这一层。

## Alkemie：从软件知识集合到向量召回

Alkemie 的入口是 `backend/agents/rag`，处理按软件组织的规则知识。其检索器根据文件后缀区分参数规则 `parameter_rules`、工作流 `workflow_patterns` 与错误模式 `error_patterns`，不是把所有上传 PDF 自动变成同一个集合。

| 源码入口 | 阅读重点 |
| --- | --- |
| [retriever.py](https://github.com/hfood02/Alkemie/blob/f3b7481df6920ab14c30a01e7a48dd565130d430/backend/agents/rag/retriever.py) | 软件范围、惰性加载、清单、检索与格式化 |
| [embeddings.py](https://github.com/hfood02/Alkemie/blob/f3b7481df6920ab14c30a01e7a48dd565130d430/backend/agents/rag/embeddings.py) | 本地或 API 向量生成、模型维度与缓存 |
| [vector_store.py](https://github.com/hfood02/Alkemie/blob/f3b7481df6920ab14c30a01e7a48dd565130d430/backend/agents/rag/vector_store.py) | FAISS 与 NumPy 后端、归一化、距离阈值 |

`RAGRetriever` 初始化保持轻量；`retrieve` 在需要时加载集合并生成查询向量。持久索引清单记录源文件 SHA-256、Embedding 提供方、模型和索引版本；源或模型变化时，缓存校验可触发重建。跨进程写锁协调 Web 与 worker 的缓存写入，清单在索引写完后才落盘。

向量后端对文档和查询做归一化，FAISS 使用 `IndexFlatL2`，分数是平方 L2 距离。`score_threshold` 是允许的最大距离，`retrieve` 按分数升序排列。这与“相似度越大越好”的接口含义不同。默认 `auto` 后端可在 FAISS 不可用时回退 NumPy；回退后的延迟与规模仍需测量。

阅读时还要检查集合参数：指定集合时返回该范围前 k 项；未指定时可以返回各集合检索结果合并后的列表，不能一概当成全库前 k 项。软件集合范围用于知识组织，若将来接入用户私有资料，还要另外设计文档授权和索引隔离。

## 怎样迁移到自己的应用

若目标是软件排障助手，可从 Alkemie 的小型规则集合起步，保留来源和适用版本；若目标是文献阅读，可参考 Archeos 的持久解析任务、页块定位和版本约束。两条链路可以共享评估问题，但不能把距离分数、块结构和权限模型直接互换。

本专题的 [Neo4j 练习](Neo4j与Cypher入门.md)与 [GraphRAG 流程](GraphRAG与混合检索.md)是进一步设计的教学示例。上述已核对模块没有显示 Neo4j 接入；若要新增图层，先定义实体、来源与失效规则，再对照现有检索基线评估，避免把新增数据库当成效果提升的证据。
