# Elasticsearch 映射与全文检索

适用环境：已有 Elasticsearch 8.x／9.x 自建或 Elastic Stack 测试服务与 Kibana Dev Tools，非 Serverless 配置。以下 HTTP 块可在 Console 中逐条执行；它们不是直接粘贴到 Shell 的命令。认证与 TLS 使用实际部署配置。

Elasticsearch 基于 Lucene 提供全文检索与聚合。把文档切成片段后，索引记录“哪些词出现在哪些片段”，查询时召回候选并排序。关系数据库中的 B-tree 索引擅长 ID、范围与排序；倒排索引面向词项匹配，两者可共同服务文献库。

## 索引、文档和 Mapping

Elasticsearch 的 index 是一组搜索文档的逻辑集合，内部由分片承载；它与 MySQL 中“加一个索引”不是同一层概念。文档是 JSON 对象，`_id` 标识索引中的记录，Mapping 定义字段的搜索行为。

下面建立全新的测试索引。索引名已存在时先检查原内容，再另取测试名：

```http
PUT handbook_chunks_v1
{
  "settings": {"number_of_shards": 1, "number_of_replicas": 0},
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "project_id": {"type": "keyword"},
      "document_id": {"type": "keyword"},
      "chunk_id": {"type": "keyword"},
      "source_version": {"type": "integer"},
      "title": {
        "type": "text",
        "fields": {"raw": {"type": "keyword", "ignore_above": 512}}
      },
      "text": {"type": "text", "analyzer": "standard"},
      "software": {"type": "keyword"},
      "page": {"type": "integer"},
      "updated_at": {"type": "date"}
    }
  }
}
```

单主分片、零副本仅用于小型单节点练习；零副本没有副本冗余，生产分片需按容量、负载和故障目标规划。`dynamic: strict` 拒绝未声明字段，帮助发现输入结构漂移。

`text` 经分析器处理，适合正文匹配；`keyword` 保留值，适合项目、软件名、精确过滤及聚合。`title.raw` 为标题提供另一种索引方式，超过 `ignore_above` 的值不进入该子字段索引。定义见官方 [text](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/text)与 [keyword](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/keyword)说明。

## 写入片段并检查可见性

```http
PUT handbook_chunks_v1/_doc/demo1-paper001-v1-c1?refresh=wait_for
{
  "project_id": "demo1",
  "document_id": "paper-001",
  "chunk_id": "paper-001:v1:1",
  "source_version": 1,
  "title": "VASP convergence notes",
  "text": "VASP SCF convergence depends on the electronic minimization settings.",
  "software": "VASP",
  "page": 3,
  "updated_at": "2026-11-07T00:00:00Z"
}
```

这是教学文本，不作为 VASP 参数选择的科学依据。`_id` 包含项目与版本，避免不同项目使用相同片段编号时互相覆盖。`refresh=wait_for` 用于本例写完后马上搜索；普通持续写入的可见性与批处理见[索引同步](Elasticsearch索引同步与重建.md)。

## 精确过滤与全文相关性分开

```http
GET handbook_chunks_v1/_search
{
  "size": 10,
  "_source": ["document_id", "chunk_id", "source_version", "title", "page", "text"],
  "query": {
    "bool": {
      "filter": [
        {"term": {"project_id": "demo1"}},
        {"term": {"software": "VASP"}}
      ],
      "must": [
        {"match": {"text": "SCF convergence"}}
      ]
    }
  }
}
```

从空索引依次执行，预期命中刚写入的片段。`match` 按字段分析器处理查询词，默认允许词项间 OR；要同时匹配词项，可配置 `operator: and`。`term` 用于已经明确的索引词项，项目编号应放在 `keyword` 字段。

`filter` 限定候选且不贡献相关性分数，`must` 参与匹配与评分，具体语义见 [bool 查询](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-bool-query)。有 filter 或 must 时，should 默认可选；若期望至少命中一个 should，明确写 `minimum_should_match`。

服务端从当前用户权限生成项目过滤，不能让浏览器自行决定可访问项目。高亮、聚合、补全与导出也需同样范围；`_source` 仅决定返回字段，不是权限控制。召回后再回源校验文档版本与权限，尤其要处理撤销访问后的索引延迟。

## 聚合与分词怎样检查

按软件统计命中片段数量：

```http
GET handbook_chunks_v1/_search
{
  "size": 0,
  "query": {"term": {"project_id": "demo1"}},
  "aggs": {"by_software": {"terms": {"field": "software", "size": 20}}}
}
```

`doc_count` 是索引文档数，此处即片段数，不是独立论文或计算次数。`terms` 默认返回前若干桶，分布式聚合还需关注误差；需要完整枚举或精确业务计数时，另选分页聚合或回源统计。

分词直接影响召回，先查看实际词项：

```http
POST handbook_chunks_v1/_analyze
{
  "field": "text",
  "text": "VASP ENCUT Ge2Sb2Te5 电子自洽"
}
```

标准分析器不等同于针对中文、化学式和错误码优化的分词器。用真实查询检查词项是否被拆散，再选择分析器、同义词或独立精确字段。可选插件需核对版本、安装条件和许可；不能通过更换名字就假定中文召回改善。

对象数组若表示“性质、数值、单位”的对应组，普通 object 的展开可能打散组内关联；需要独立匹配数组元素时核对 [nested 建模](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/nested)。片段返回给 RAG 前，保留来源版本、页码及表格上下文，继续参考[RAG 评估](../../知识工程/RAG检索生成与评估.md)。
