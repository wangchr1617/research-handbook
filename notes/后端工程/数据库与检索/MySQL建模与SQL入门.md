# MySQL 建模与 SQL 入门

适用环境：已运行的 MySQL 8.4，使用 InnoDB；命令在本机终端与 MySQL 客户端执行。MariaDB 与其他数据库需另行核对语法、驱动和行为。

科研应用常要同时保存“谁的资料、哪一版文件、现在处理到哪一步”。MySQL 用表表示这些对象，通过主键、唯一键和事务维持一致性。PDF 和大型轨迹一般存文件或对象存储，表中记录路径、内容哈希与版本；这样可以按权限查元数据，也能回到原文件。

## 连接与准备练习库

先按[官方安装说明](https://dev.mysql.com/doc/refman/8.4/en/installing.html)准备服务，并取得可创建练习库的账号。数据库在本机时可这样连接，`-p` 会交互提示密码：

```bash
mysql --host=127.0.0.1 --port=3306 --user=YOUR_TEST_USER -p
```

远程服务的 TLS、地址和凭据按管理员提供的方式配置。先核对实际版本与事务配置：

```sql
SELECT VERSION(), @@transaction_isolation, @@autocommit;
CREATE DATABASE handbook_demo
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE handbook_demo;
```

以下首次建表练习使用新库。默认排序规则适合一般文本；文件哈希和内部 ID 若需区分大小写，应选择明确的二进制排序规则，不能让显示名称的比较规则决定标识符是否相同。

## 让表结构表达数据边界

```sql
CREATE TABLE projects (
  id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  name VARCHAR(200) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE documents (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  project_id BIGINT UNSIGNED NOT NULL,
  source_key VARCHAR(128) COLLATE utf8mb4_bin NOT NULL,
  title VARCHAR(500) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'queued',
  source_version INT UNSIGNED NOT NULL DEFAULT 1,
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_document_project FOREIGN KEY (project_id)
    REFERENCES projects(id),
  CONSTRAINT uq_document_source UNIQUE (project_id, source_key),
  CONSTRAINT ck_document_status CHECK
    (status IN ('queued', 'processing', 'ready', 'failed')),
  CONSTRAINT ck_source_version CHECK (source_version >= 1),
  INDEX ix_project_status_id (project_id, status, id)
) ENGINE=InnoDB;

INSERT INTO projects (id, name) VALUES (1, '教学项目');
INSERT INTO documents (project_id, source_key, title)
VALUES (1, 'paper-001', 'VASP SCF convergence notes');
```

主键定位记录，外键防止引用不存在的项目，唯一键约束项目内的来源编号，CHECK 限制状态和值域。MySQL 8.4 执行 CHECK；不能用早期版本“接受语法”的经验推断约束已经生效，具体规则见[官方 CHECK 文档](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html)。

表中的项目字段供查询定位，用户是否属于该项目仍由认证与授权逻辑校验。若后续片段表同时保存 `project_id` 和 `document_id`，需通过复合引用或业务校验保证它们指向同一项目。

## 查询、更新与连接

```sql
SELECT d.id, p.name, d.title, d.status
FROM documents AS d
JOIN projects AS p ON p.id = d.project_id
WHERE d.project_id = 1
ORDER BY d.id;

UPDATE documents
SET status = 'ready'
WHERE project_id = 1 AND source_key = 'paper-001';
```

从空白练习库按顺序执行，第一次 SELECT 应得到一条 `queued` 文档；UPDATE 后重新查询应变为 `ready`。缺失记录用 `IS NULL` 判断，`NULL` 表示缺失或未知，不等同于空字符串或零。

固定每页 20 条的首次查询可以按 `id DESC` 排序；下一页增加 `id < 上页最小ID`。这类游标分页避免深 OFFSET 扫描，适用于主键排序；若按更新时间排序，游标需同时包含时间和唯一 ID，处理相同时间及分页期间的更新。

## 应用代码绑定参数

下面是 PyMySQL 的完整只读片段，依赖已有的 `pymysql` 包。环境变量由自己的配置或凭据管理方式提供：

```python
import os
import pymysql

connection = pymysql.connect(
    host=os.environ['MYSQL_HOST'],
    port=int(os.environ.get('MYSQL_PORT', '3306')),
    user=os.environ['MYSQL_USER'],
    password=os.environ['MYSQL_PASSWORD'],
    database='handbook_demo', charset='utf8mb4',
)
try:
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT id, title FROM documents '
            'WHERE project_id=%s AND status=%s ORDER BY id DESC LIMIT %s',
            (1, 'ready', 20),
        )
        print(cursor.fetchall())
finally:
    connection.close()
```

`%s` 由驱动处理，不使用 Python 字符串格式化拼接用户输入。字段名和排序方向通过服务端白名单选择，不能把整段客户端 SQL 当参数执行。生产连接还应补上 TLS 与超时设置；驱动示例参见 [PyMySQL 官方用法](https://pymysql.readthedocs.io/en/latest/user/examples.html)。

下一步阅读[事务、锁与索引](MySQL事务锁与索引.md)，理解同一条文档被两个 worker 同时修改时如何保持状态正确。
