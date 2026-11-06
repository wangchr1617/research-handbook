# Archeos 与 ALKEMIE 源码阅读

**适用环境：通用；阅读 Python／TypeScript 源码无需部署。实际运行应遵循对应项目的依赖锁、平台要求与部署文档。**

## 从一次请求开始读

Archeos 提供科研工作台与运行时网关，ALKEMIE 包含科研工具、用户会话和 Agent 集成。阅读时沿“路由 → 输入模型 → 身份与权限 → 服务／引擎 → 持久化 → 响应”追踪一条请求，比逐个文件顺序翻阅更容易理解。

本篇源码链接固定在 Archeos `275ee9c5edcf4df6c773512d8576cb0010168fd4` 和 ALKEMIE `46bd55237fa01bf30fa65c7ae99bcbb6b4eca8a6`。后续版本可能改变路径、认证方式和数据模型。下表说明所链接源码的职责；部署行为与隔离效果需在目标环境分别验证。

## Archeos：HTTP、认证与配置

| 入口 | 观察重点 | 对应笔记 |
| --- | --- | --- |
| [`backend/pyproject.toml`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/pyproject.toml) | Python 3.12+、FastAPI、SQLAlchemy、Pydantic Settings 等依赖 | [项目组织](../接口与安全/项目组织配置异常与日志.md) |
| [`archeos/app.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/app.py) | lifespan、路由组装、Origin 检查、请求 ID、错误边界 | [异常与日志](../接口与安全/项目组织配置异常与日志.md) |
| [`archeos/schemas.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/schemas.py) | `Input` 禁止额外字段，`Credentials` 与响应模型分开 | [参数校验](../接口与安全/HTTP接口与参数校验.md) |
| [`archeos/config.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/config.py) | `ARCHEOS_` 前缀、`.env`、`SecretStr`、超时与预算 | [配置](../接口与安全/项目组织配置异常与日志.md) |
| [`archeos/auth.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/auth.py) | `login`、`issue_session`、登录尝试计数、退出和改密撤销 | [认证](../接口与安全/用户认证权限与Agent安全.md) |
| [`archeos/security.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/security.py) | `current_user` 校验会话和 CSRF，`membership` 校验团队成员 | [权限](../接口与安全/用户认证权限与Agent安全.md) |

阅读练习：从 `auth.py::login` 找到 `Credentials`，再追踪 `issue_session` 写入的字段，最后看 `security.py::current_user` 如何验证这些字段。注意身份不是前端提交的角色；权限检查也不只是“已经登录”。

## Archeos：持久化、流式与任务

| 入口 | 观察重点 |
| --- | --- |
| [`archeos/db.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/db.py) | Session 生命周期、SQLite 外键／WAL／busy timeout、Alembic 迁移 |
| [`archeos/models.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/models.py) | User、Member、LoginSession、ResourceGrant、ScientificTask 与 ScientificContinuation |
| [`archeos/engine/routes.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/engine/routes.py) | `events` 的资源授权、cursor、周期性会话检查、断开处理；`upload` 的附件入口 |
| [`archeos/streaming.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/streaming.py) | `close_iterator` 与 `ResourceStreamingResponse` 的资源收尾 |
| [`archeos/scientific_tasks.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/scientific_tasks.py) | `record_task_intent` 保存唯一意图，`_authorized` 重查成员与 grant，`reconciliation_loop` 周期核对 |
| [`archeos/runtime_policy.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/runtime_policy.py) | 服务端控制递归／token 上限，配置预算与执行权限分别处理 |
| [`scientific_compute/execution_policy.py`](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/packages/scientific-compute/scientific_compute/execution_policy.py) | 执行时重读策略；多用户不可信模式拒绝较弱执行器 |

这里 `models.py` 保存平台身份与任务元数据，研究运行状态还会由引擎与计算服务管理。不要仅凭该文件缺少 Message 表，就推断项目没有历史持久化；也不要把本专题 Demo 的 `conversations/messages/run_events` 表说成原项目现有表结构。

对照[流式响应](流式响应与前端基础.md)：查找 `events` 中创建的 pending task、超时等待与 `finally`。思考如果浏览器断开、用户被撤销或上游抛错，谁负责关闭迭代器？

对照[后台任务](../并发与任务/后台任务队列与恢复.md)：查找 `record_task_intent` 的唯一身份和授权检查，再观察 reconciliation 与 HTTP 查询之间的分工。本专题引入 Redis／Celery 是独立教学选型，不据此推断原项目采用 Celery。

## ALKEMIE：会话撤销与流式恢复

| 入口 | 观察重点 |
| --- | --- |
| [`backend/auth/session_service.py`](https://github.com/hfood02/Alkemie/blob/46bd55237fa01bf30fa65c7ae99bcbb6b4eca8a6/backend/auth/session_service.py) | refresh token 摘要、有效期、轮换、`revoke_user_sessions` |
| [`backend/agents/stream_recovery.py`](https://github.com/hfood02/Alkemie/blob/46bd55237fa01bf30fa65c7ae99bcbb6b4eca8a6/backend/agents/stream_recovery.py) | scope、room、进程内锁、事件数量上限与终态 TTL |
| [`backend/agents/streaming.py`](https://github.com/hfood02/Alkemie/blob/46bd55237fa01bf30fa65c7ae99bcbb6b4eca8a6/backend/agents/streaming.py) | 流事件规范化、追踪压缩与持久化前的格式处理 |

`AgentStreamRecoveryStore` 的说明明确区分：完成轮次以会话文件为持久事实来源，排队／流式过程使用有界的进程内快照。它通过 `RLock` 保护后台线程与订阅处理器共享状态，并按作用域隔离流。

这个快照能缓解历史查询与实时订阅的竞态，但进程退出会丢失，多个进程也不会自动共享。若改成多 worker 部署，需要共享事件存储和明确重放协议；把字典机械替换成 Redis 键并不能自动完成恢复设计。

## 迁移为自己的 Demo

1. 从输入模型与身份检查开始，先验证未登录、越权、未知字段和超长输入。
2. 独立设计自己的会话／消息／run 表，不依赖私有运行目录或现有管理员账号。
3. 用固定工具替代模型，先跑通状态机与故障分支。
4. 在工具适配层接入所用模型，传播 `run_id`、期限和取消信号，限制调用次数、输出与费用。
5. 使用两个不同账号验收完整链路，再做 worker／broker／数据库故障练习。

对应的独立实现见 [Agent Demo](../../../examples/backend/agent-demo/README.md)。它借鉴职责划分，没有复制两项目的运行环境、密钥和用户数据。

## 按调用顺序追踪，而不是停在文件清单

可以选择以下三条线，每条线只追踪一个具体问题：

| 线索 | 依次阅读 | 应能解释的结果 |
| --- | --- | --- |
| 登录后发送写请求 | Credentials → login → issue_session → app.boundary → current_user | 密码、Cookie、Origin、CSRF 分别在哪校验 |
| 一个 run 的流 | events → runtime／grant → engine.stream → pending → close_iterator | 断开和权限撤销怎样结束订阅 |
| 科研任务后续执行 | ScientificTask → record_task_intent → reconciliation_loop → continuation receipt | 唯一意图、授权复查、核对与重试如何区分 |

### 一段真实的登录校验

[auth.py::login](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/auth.py) 完整函数：

```python
@router.post("/login", response_model=LoginView)
def login(body: Credentials, request: Request, response: Response, db: DB):
    key = record_attempt(db, request, body.email)
    user = db.scalar(select(User).where(User.email == body.email))
    ok = check_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not ok or not user.active:
        fail("invalid_credentials", 401)
    db.execute(delete(LoginAttempt).where(LoginAttempt.key == key))
    return issue_session(db, response, user)
```

`record_attempt` 在校验密码前执行，使失败尝试也计入预算；不存在用户时仍走 DUMMY_HASH 校验路径，减少直接跳过密码计算造成的时间差；有效用户也必须 active。成功之后不是返回数据库 User 原对象，而是由 `issue_session` 创建会话并返回 LoginView。

该函数挂在 auth router 下，完整 URL 还要看 app.include_router 的 prefix；不能仅把装饰器里的 `/login` 当成对外路径。Demo 的 `/api/auth/login` 与这里的原项目路径和输入字段均不同。

### ALKEMIE 的 scope 是如何形成的

[stream_recovery.py::agent_stream_scope](https://github.com/hfood02/Alkemie/blob/46bd55237fa01bf30fa65c7ae99bcbb6b4eca8a6/backend/agents/stream_recovery.py) 的完整函数：

```python
def agent_stream_scope(project_id: str, user_id: str | None) -> str:
    """Return the isolation key used by recovery state and Socket.IO rooms."""
    normalized_project_id = str(project_id or "temp")
    if is_user_scoped_agent_context_id(normalized_project_id):
        return f"user:{str(user_id or '')}:session:{normalized_project_id}"
    return f"project:{normalized_project_id}"
```

用户级会话的恢复键同时包含 user 与 session，项目级上下文使用项目键。是否允许某个用户订阅对应 project／session，还需要上游鉴权；生成一个 room／scope 字符串本身不等于授权完成。接着读注册、更新和清理快照的调用方，确定每个入口传入的 user_id 来自可信认证上下文。

`AgentStreamRecoveryStore` 的 RLock 只保护同进程中的线程。跨进程部署后，相同字符串 scope 不会让多个 Python 字典自动同步；共享事件存储与消费协议必须另行实现。

## 把阅读结果映射到自己的代码

| 原项目中的职责 | 本仓库可运行入口 | 练习输入 |
| --- | --- | --- |
| 输入类与响应模型 | `demo/schemas.py`、`main.py` | `run-normal.json`、`run-invalid.json` |
| 当前身份与资源权限 | `demo/security.py` | 案例脚本自动创建的两个账号 |
| 持久意图和核对 | `demo/jobs.py` | `run-retry.json`、过期 deadline 故障注入 |
| 流式上游资源管理 | `main.py::events`、`index.html::stream` | 案例输出的 `normal-events.sse` |
| 外部工具 I/O | HTTP 工具服务和并发客户端 | `tools-normal/partial/deadline.json` |

这些映射用于迁移工程思路，不表示字段名、认证方案和任务协议相同。阅读时记录“函数输入、校验条件、副作用、持久化点、失败分支、清理动作”六项，再尝试用输入文件触发每个分支，才能从看懂名称走到理解行为。
