# Neo4j 与 Cypher 入门

适用环境：已准备的 Neo4j 5.x 或兼容后续版本测试数据库；Python 驱动示例使用提供 `execute_query` 的版本。先在隔离的空白练习库操作，记录服务器与驱动版本。

Neo4j 保存属性图：节点表示文献、片段或材料，关系表示包含、引用和研究对象，属性保存标识、标题、页码等字段。Cypher 用图模式表达查询。想按多层关系寻找证据时，可直接写出需要匹配的路径。

## 准备连接

可通过 Neo4j Desktop 创建本机测试库，或使用已有测试服务。启动后记录 Bolt URI、数据库名和账号，使用 Neo4j Browser 执行下列 Cypher。服务准备见[官方入门](https://neo4j.com/docs/getting-started/)。Python 接入还需要在自己的虚拟环境安装 `neo4j` 包，并通过环境变量提供凭据。

下面建立一个名为 `demo` 的教学项目及一篇文档、一个片段。`demo` 是节点属性中的项目编号，和 Neo4j 数据库名是两个概念。

## 先定义唯一标识，再导入

在测试库依次执行：

```cypher
CREATE CONSTRAINT paper_key IF NOT EXISTS
FOR (p:Paper) REQUIRE (p.project_id, p.id) IS UNIQUE;

CREATE CONSTRAINT chunk_key IF NOT EXISTS
FOR (c:Chunk) REQUIRE (c.project_id, c.id) IS UNIQUE;
```

复合唯一约束让同一项目内的文档或片段 ID 唯一；缺少约束属性的节点不受这项唯一性规则约束，因此应用还需校验必填字段。[官方约束说明](https://neo4j.com/docs/cypher-manual/current/schema/constraints/create-constraints/)解释了这一行为。

```cypher
MERGE (p:Paper {project_id: 'demo', id: 'paper-001'})
SET p.title = '教学文档', p.version = 'v1'
MERGE (c:Chunk {project_id: 'demo', id: 'paper-001:v1:1'})
SET c.text = '教学片段：该段用于说明证据定位。',
    c.page = 3, c.version = 'v1'
MERGE (p)-[:HAS_CHUNK]->(c);
```

`MERGE` 根据给出的模式匹配或创建，`SET` 更新属性。把可变标题放进 `MERGE` 身份模式，会使改标题变成新建实体；先按稳定键找到节点，再更新内容。并发导入还需唯一约束保护，详见 [MERGE 手册](https://neo4j.com/docs/cypher-manual/current/clauses/merge/)。

以上例子重复执行后，查询应仍只有一行：

```cypher
MATCH (p:Paper {project_id: 'demo', id: 'paper-001'})
      -[:HAS_CHUNK]->(c:Chunk {project_id: 'demo'})
RETURN p.title AS title, c.id AS chunk_id, c.page AS page;
```

预期 `chunk_id` 为 `paper-001:v1:1`，页码为 `3`。这验证了示例的重复导入行为；实际应用还要检查缺失字段、版本更新与事务失败后的重试。

## Python 中使用参数

设置 `NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD` 和 `NEO4J_DATABASE` 后运行。URI 使用服务实际给出的协议与地址。下面只读查询，不修改图数据：

```python
import os
from neo4j import GraphDatabase

with GraphDatabase.driver(
    os.environ['NEO4J_URI'],
    auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']),
) as driver:
    driver.verify_connectivity()
    records, summary, keys = driver.execute_query(
        "MATCH (p:Paper {project_id: $project, id: $paper})"
        "-[:HAS_CHUNK]->(c:Chunk {project_id: $project}) "
        "RETURN c.id AS id, c.text AS text, c.page AS page LIMIT 20",
        project='demo', paper='paper-001',
        database_=os.environ['NEO4J_DATABASE'],
    )
    print([record.data() for record in records])
```

查询结构与参数值分开，便于复用执行计划，也避免把用户输入直接拼入查询。连接和驱动用法见 [Python Driver 手册](https://neo4j.com/docs/python-manual/current/query-simple/)。服务端应从登录上下文得到项目范围，再校验资源访问权；上面硬编码的 `demo` 仅供练习。

## 图建好了以后查什么

引入[知识建模笔记](知识图谱与科研知识建模.md)中的 Observation 后，可以查“某材料的结果来自哪篇文献、哪次计算”。控制路径类型和跳数，分别约束起点、终点及中间证据的访问范围。只限制返回条数无法限制前面的图遍历成本，复杂查询需查看执行计划并设置期限。

当节点有多份文献支持或存在冲突时，保存独立证据节点或带来源的断言节点。向量索引解决文本相近问题，图路径解决已记录的关系问题，二者在 [GraphRAG](GraphRAG与混合检索.md)中可以结合。这里的 Neo4j 模型是教学扩展，两个项目的已核对知识模块见[源码实例](Archeos与Alkemie的知识链路.md)。
