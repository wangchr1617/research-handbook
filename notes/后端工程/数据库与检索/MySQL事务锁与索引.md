# MySQL 事务、锁与索引

适用环境：MySQL 8.4、InnoDB；SQL 使用[建模入门](MySQL建模与SQL入门.md)中的 `handbook_demo`。并发练习需要两个独立客户端连接。

一次任务完成可能涉及结果记录、文档状态和待同步事件。把这些数据库写入放在同一事务，可让它们一起提交或回滚；调用模型、解析 PDF 和写搜索索引则发生在事务外，避免长时间持锁。

## 事务边界和隔离级别

```sql
USE handbook_demo;
START TRANSACTION;
UPDATE documents SET status = 'processing'
WHERE project_id = 1 AND source_key = 'paper-001';
ROLLBACK;
```

执行前后查询状态，应保持原值。`COMMIT` 才提交事务，默认自动提交模式下，单独一条普通 DML 通常是一个事务。建表、改表等 DDL 常造成隐式提交，不能把 `ALTER TABLE` 放进普通业务事务后期待 ROLLBACK 撤销，见[隐式提交说明](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html)。

InnoDB 默认隔离级别为 REPEATABLE READ；普通一致性读与锁定读有不同语义。MVCC 让普通读可读取符合快照的版本，锁定读则用于协调当前记录的并发修改。隔离级别、查询条件与索引还会影响记录锁、间隙锁及 next-key lock，详见[事务隔离级别](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)。

因此，应按语句类型判断读写行为。“同一事务普通 SELECT 两次看到相同内容”不能推广到所有读写语句，提高隔离级别也不能自动消除业务竞争。

## 两个 worker 怎样争抢同一项任务

任务领取可以用条件更新：

```sql
UPDATE documents SET status = 'processing'
WHERE project_id = 1 AND source_key = 'paper-001'
  AND status = 'queued';
SELECT ROW_COUNT();
```

只有受影响行数为 1 的领取者继续处理，0 表示没有领取到。它解决一次状态转换竞争；完整任务系统仍需尝试代次、租约或恢复策略，以处理 worker 领取后退出的情况。

若需要先读状态再更新，可以在同一短事务中使用锁定读。连接 A 执行：

```sql
START TRANSACTION;
SELECT id, status FROM documents
WHERE project_id = 1 AND source_key = 'paper-001'
FOR UPDATE;
```

连接 B 对同一行的 UPDATE 会等待相应锁释放；连接 A 执行 COMMIT 后再观察 B。配置、其他锁或等待超时可能影响实际结果。

可用 `SKIP LOCKED` 构造队列领取，但跳过锁定行不提供一致的全量视图，也不保证公平调度，见[锁定读手册](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html)。

死锁是多个事务相互等待形成环。缩短事务、按固定顺序访问资源、为筛选条件建立适当索引能减少发生概率。收到死锁错误后，回滚并有限重试整个幂等事务；锁等待超时的回滚范围另行核对，统一回滚当前应用事务更容易恢复明确状态。[官方处理建议](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks-handling.html)说明了重试与监测方式。

## 从实际查询决定联合索引

示例表有 `(project_id, status, id)` 索引，适合在项目和状态确定后按 ID 取一页：

```sql
EXPLAIN
SELECT id, title FROM documents
WHERE project_id = 1 AND status = 'ready' AND id < 1000
ORDER BY id DESC LIMIT 20;
```

联合索引的最左前缀可支持按前导列定位。只按 `status` 查询，不能把该索引当作以 `status` 开头的高效查找保证；优化器仍可能选择索引扫描或其他策略。范围条件后的列能否参与过滤、排序或覆盖，要看具体执行计划，见[多列索引](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html)。

关注使用的 key、估计扫描行数、过滤和排序方式；`EXPLAIN ANALYZE` 会实际运行受支持的语句并报告实测信息，应先在测试数据上使用。小表选择全表扫描可能更便宜，不要把“未用索引”直接判为错误。执行计划说明见[官方 EXPLAIN 文档](https://dev.mysql.com/doc/refman/8.4/en/explain.html)。

索引会增加存储、写入和维护成本。先保存典型查询和数据分布，再比较延迟及扫描量；对 SQL 中的函数、隐式类型转换和 `%term%` 搜索，逐项检查是否阻碍有效查找。文档全文相关性搜索可以进一步使用[Elasticsearch](Elasticsearch映射与全文检索.md)。
