# Elasticsearch 索引同步与重建

适用环境：Elasticsearch 8.x／9.x 测试服务；HTTP 块在 Kibana Dev Tools 执行。示例延续[映射与检索](Elasticsearch映射与全文检索.md)的 `handbook_chunks_v1`，同步架构是教学设计。

关系数据库提交后，搜索索引可能尚未更新；索引写入成功后，搜索也可能需要等待 refresh。应用应分别记录业务事务是否提交、索引操作是否成功，以及当前索引是否满足查询所需版本。

## refresh、持久性与搜索可见性

Elasticsearch 是近实时搜索。`refresh` 使新变更可搜索，不能把它当成备份或跨系统事务提交。默认写入通常不等下一次 refresh；`refresh=wait_for` 等待相关变更可搜索，适合交互式小批操作。大量逐条强制 `refresh=true` 会增加小 segment 与合并负担，见[官方 refresh 参数](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/refresh-parameter)。

如果索引设置关闭了定时 refresh，`wait_for` 可能持续等待其他 refresh 来源。先检查索引配置和调用期限，再判断“写入卡住”是推理、网络还是可见性等待。

## 用 Bulk 批量写入

Bulk 请求使用 NDJSON，一行操作描述、一行文档体，最后一行必须有换行。Console 示例：

```http
POST _bulk?refresh=wait_for
{"index":{"_index":"handbook_chunks_v1","_id":"demo1-paper001-v1-c2"}}
{"project_id":"demo1","document_id":"paper-001","chunk_id":"paper-001:v1:2","source_version":1,"title":"VASP convergence notes","text":"Teaching example: inspect the convergence log.","software":"VASP","page":4,"updated_at":"2026-11-07T00:00:00Z"}
```

通过 HTTP 客户端发送时使用 `application/x-ndjson`，保留逐行格式及末尾换行。HTTP 成功不代表每条成功：检查响应的 `errors` 和各 item 的 status、error，仅重试适合重试的失败项。字段类型错误先修输入，429 等暂时性错误采用退避并限制重试，详见 [Bulk API](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-bulk)。

固定 `_id` 能防止同一条索引写入生成重复记录，但不能防止旧事件覆盖新内容。任务版本、事件顺序和删除传播需要另外处理。

## 数据库与搜索怎样可靠同步

同时“提交 MySQL，再写 Elasticsearch”会遇到部分成功：数据库成功但索引失败，或者客户端超时后无法判断写入结果。可以采用事务发件箱：

1. 在同一个 MySQL 事务中保存文档新状态与 outbox 事件。
2. worker 读取事件，按稳定实体 ID 和源版本生成搜索文档。
3. 索引返回逐项成功后，再确认事件已处理；失败可重试或进入待人工处理状态。
4. 定期对照源版本、内容哈希与索引检查点，补齐遗漏及清理旧片段。

这通常提供至少一次投递，消费者需要幂等。事件字段包含实体、单调递增版本、操作类型和内容摘要；同一实体的更新和删除要有顺序保障。可使用分区顺序处理、持久版本账本或经过验证的外部版本控制方案，不能把“去重事件 ID”当成完整乱序保护。

删除时记录墓碑及其版本，直到足够覆盖重放窗口；否则延迟到达的旧更新可能复活内容。文档 v2 若比 v1 少几个片段，除写入新块，还要删除或排除旧版本块。用户权限撤销应立即由权威权限存储生效，不能等待索引同步后才限制读取。

已有 CDC 基础设施时，也可通过 binlog 捕获变更；仍需设计初始快照、增量衔接、DDL、位点恢复和删除。数据库事务与搜索索引之间的最终一致性是系统契约，应体现在“处理中、索引就绪”等用户可理解的状态中。

## Mapping 改变后怎样重建

已有字段类型通常不能直接改成另一种。创建 `handbook_chunks_v2` 并明确 Mapping、分析器和分片配置，再导入或重建。`_reindex` 不负责自动复制源索引全部设置，也不替代并发写入的增量追赶，见 [Reindex API](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-reindex)。

应用通过别名 `handbook_chunks` 访问，首次绑定可执行：

```http
POST _aliases
{
  "actions": [
    {"add": {"index": "handbook_chunks_v1", "alias": "handbook_chunks"}}
  ]
}
```

重建期间先固定导出水位，再追赶增量及删除，抽查数量、源版本、权限和检索结果。新索引准备完成后才切换。下面是条件示意，要求 v2 已存在、增量已追平、别名当前仅绑定 v1：

```http
POST _aliases
{
  "actions": [
    {"remove": {"index": "handbook_chunks_v1", "alias": "handbook_chunks"}},
    {"add": {"index": "handbook_chunks_v2", "alias": "handbook_chunks"}}
  ]
}
```

两项在同一次别名变更中提交，执行后检查动作错误及最终绑定，参见[别名文档](https://www.elastic.co/docs/manage-data/data-store/aliases)。别名切换只能切换访问目标，不能补齐缺失数据；旧索引若已停止接收增量，也不能直接切回就保证数据完整。

## 分页、监控和恢复

浅分页可使用 `from` 与 `size`，深分页优先按固定排序使用 PIT 和 `search_after`。把上一页返回的完整 sort 值传入下一页，并沿用 PIT；没有稳定快照与唯一排序时可能重复或漏项。PIT 会占用资源，及时关闭，示例见[分页手册](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/paginate-search-results)。

持续观察索引延迟、拒绝写入、磁盘水位、堆内存、分片状态和查询延迟。单节点配置副本却无其他节点时可能 yellow；这与主分片丢失导致不可用的 red 含义不同。

副本承担可用性，快照承担备份；用 Elasticsearch 支持的 [snapshot／restore 流程](https://www.elastic.co/docs/deploy-manage/tools/snapshot-and-restore)，数据目录复制不能作为受支持的恢复方案。若源资料与处理配置完整，也可重建派生索引，但要测量重建时间是否满足恢复目标。
