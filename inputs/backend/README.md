# 后端工程练习输入

**适用环境：Python 3.12；Linux、macOS 或 Windows WSL。HTTP 输入对应本仓库 Agent Demo，不直接对应 Archeos／ALKEMIE 的完整业务接口。**

| 文件 | 用途 | 关键结果 |
| --- | --- | --- |
| [conversation.json](conversation.json) | 创建“研究笔记统计”会话 | 201，得到会话 ID |
| [run-normal.json](run-normal.json) | 正常执行，5 秒期限 | succeeded，attempt=1 |
| [run-retry.json](run-retry.json) | 一次瞬时故障 | retry_wait 后由 dispatcher 再投递 |
| [run-timeout.json](run-timeout.json) | 工具等待超过 1 秒期限 | timed_out |
| [run-failure.json](run-failure.json) | 不可重试错误 | failed |
| [run-invalid.json](run-invalid.json) | 错误类型、未知字段 | 422，不创建 run |
| [研究笔记样例.md](研究笔记样例.md) | UTF-8 附件；原文件 226 字节 | 与 normal prompt 合并为 140 字符、14 个空白分词项 |
| [tools-normal.json](tools-normal.json) | 两个独立 HTTP 工具 | words=6、characters=35 |
| [tools-partial.json](tools-partial.json) | 局部超时与 HTTP 503 | 部分成功，其余明确报告失败类别 |
| [tools-deadline.json](tools-deadline.json) | 整组期限 | deadline_exceeded |
| [查看任务.sql](查看任务.sql) | 查看教学库状态、消息和事件计数 | 不查询密码与登录凭据 |
| [固定窗口限流.lua](固定窗口限流.lua) | Redis 原子计数＋首次过期 | 递增计数，窗口单位秒 |
| [按持有者释放锁.lua](按持有者释放锁.lua) | Redis 比较 owner 后释放 | 防止删掉他人的新锁 |

任务文件的 `client_key` 故意固定，便于重复提交观察幂等。创建新的逻辑任务应更换此键；不能只改 prompt 却复用同一键。上传文件后把服务端返回的附件 ID 写入任务的 `attachment_id`，不要在模板里编造 ID。

完整步骤见[请求与恢复实操](../../examples/backend/agent-demo/请求与恢复实操.md)，概念与源码解读见[后端笔记](../../notes/后端工程/README.md)。
