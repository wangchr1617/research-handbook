# 数据库与检索

按学习顺序阅读：[阅读目录](阅读目录.md)。

关系数据库保存用户、权限、文档版本和任务状态，搜索引擎组织文本检索与聚合。本节用科研文档库说明 MySQL 和 Elasticsearch 的分工，承接[Agent 数据建模与 Redis](../并发与任务/Agent数据建模与Redis.md)，并连接[知识工程](../../知识工程/README.md)。

| 笔记 | 学习重点 |
| --- | --- |
| [科研应用的数据存储与检索选型](科研应用的数据存储与检索选型.md) | MySQL、Elasticsearch、Redis、Neo4j 与 RAG 怎样配合 |
| [MySQL 建模与 SQL 入门](MySQL建模与SQL入门.md) | 表、约束、连接查询、分页和参数绑定 |
| [MySQL 事务、锁与索引](MySQL事务锁与索引.md) | 并发更新、隔离级别、死锁和执行计划 |
| [MySQL 备份与日常运维](MySQL备份与日常运维.md) | 连接配置、账号权限、备份恢复和监控 |
| [Elasticsearch 映射与全文检索](Elasticsearch映射与全文检索.md) | 倒排索引、分词、Mapping、Query DSL 与聚合 |
| [Elasticsearch 索引同步与重建](Elasticsearch索引同步与重建.md) | 近实时可见性、Bulk、版本、别名和重建 |

MySQL 示例以 8.4、InnoDB 为基准；Elasticsearch 示例采用 8.x／9.x 共有的无类型 REST 接口，具体版本与部署差异见各篇。文档、项目 ID 和数值均为教学数据，操作应在独立练习库与测试索引中完成。外部资料核对日期为 2026-11-07。
