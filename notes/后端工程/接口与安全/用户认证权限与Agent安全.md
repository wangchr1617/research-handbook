# 用户认证、权限与 Agent 安全

**适用环境：通用；示例对应 FastAPI 与独立教学 Demo。公开部署需要 HTTPS 和入口访问控制。**

## 认证与授权分别回答什么

认证回答“请求者是谁”，授权回答“他可以对哪个资源执行什么操作”。用户 A 登录成功，不意味着可以读用户 B 的会话、下载 B 的文件或取消 B 的任务。模型声称“我是管理员”也不能成为授权依据。

常见认证方案如下：

| 方案 | 工作方式 | 需要处理的问题 |
| --- | --- | --- |
| 服务端会话＋Cookie | 浏览器带随机会话令牌，服务器查会话记录 | Cookie 属性、CSRF、过期与撤销 |
| 不透明 Bearer token | 客户端在 `Authorization` 中主动携带随机令牌 | 安全保存、有效期、摘要存储与撤销 |
| JWT | 服务端验证签名和声明 | 算法白名单、签发方、受众、过期、密钥轮换与撤销 |
| OIDC 登录 | 通过身份提供方完成登录 | 正确的重定向、state／nonce、PKCE、账号绑定 |

JWT 的 payload 通常是编码而非加密，不能放密码或模型密钥。自建用户名密码 Demo 可以使用服务端会话；团队应用更适合接入已有身份系统。密码哈希与 Bearer 认证的基础用法见 [FastAPI 安全教程](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)。

## 密码与会话生命周期

1. 创建账号时验证用户名和密码策略，用 Argon2 等密码哈希算法保存，不存明文或可逆加密密码。
2. 登录时校验哈希，失败统一返回 `invalid_credentials`，限制按账号和来源的尝试频率。
3. 成功后生成高熵随机令牌，只保存 SHA-256 摘要、用户 ID、到期时间；令牌明文只交给客户端。
4. 每次请求检查会话是否存在、是否过期、用户是否有效。
5. 退出或修改密码时撤销会话；流式长连接也需要周期性复查，而非只在连接建立时认证。

随机令牌的摘要与密码哈希用途不同：令牌有足够熵，可以用快速摘要查询；人类密码需要抵抗离线穷举，不能直接用 SHA-256。

Archeos 的 `auth.py::issue_session` 创建会话，`security.py::current_user` 验证 Cookie 和 CSRF；Demo 的 `security.py` 改用不透明 Bearer token 便于 `curl` 与 Fetch 练习。Demo 通过管理命令创建账号，网页只提供登录，不开放公共注册。

## Cookie、CSRF、CORS 与 XSS

Cookie 会自动随匹配请求发送。生产登录 Cookie 应设置 `HttpOnly`、`Secure`、合适的 `SameSite`、路径与有效期；写操作还应验证 CSRF token，并按部署方式检查 Origin。`HttpOnly` 防止脚本直接读 Cookie，但页面上的 XSS 仍可借用户身份发请求。

Bearer token 由脚本主动放请求头，常见跨站表单无法自动带上它；Demo 不使用认证 Cookie，并把令牌保存在页面内存，刷新后重新登录。不要为了方便把长期令牌放 URL、日志或共享浏览器存储。

CORS 控制浏览器是否允许跨源脚本读取响应，不是服务端认证机制。跨源 Cookie 请求需要明确允许的 Origin 和凭据策略；不能把 `*` 当作可信来源列表。用户可控内容用 `textContent` 或默认转义渲染，慎用 `innerHTML` 与 React 的 `dangerouslySetInnerHTML`。

## 每个入口都做资源授权

参照 Archeos 的 `membership` 和资源 grant 思路，最小的用户级会话检查可以写成：

```python
from fastapi import HTTPException
from sqlalchemy import select

def own_conversation(db, conversation_id, current_user_id):
    row = db.scalar(select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user_id,
    ))
    if row is None:
        raise HTTPException(404, "not_found")
    return row
```

`Conversation` 来自应用模型。创建任务、读历史、上传、下载、任务查询、取消和事件流都要复用检查。worker 接收服务器写入的 `run_id`，重新读取所属会话与工具权限；不要信任用户在 JSON 里填的 `user_id`、角色或工具凭据。

多人课题组可以增加团队成员表与角色：成员读取自己的资源，管理员管理团队配置，平台管理员管理平台。角色不应默认赋予读取其他人的模型密钥权限。对修改、删除、提交计算等能力分别授权，避免一个笼统的 `is_admin` 包揽所有权限。

## 读真实实现：Archeos 怎样识别当前用户

下面摘录 [security.py::current_user](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/security.py)，它依赖原项目的 DB、fail 与模型定义：

```python
def current_user(request: Request, db: DB) -> User:
    record = db.get(LoginSession, digest(request.cookies.get("archeos_session", "")))
    if not record or record.expires <= time.time():
        fail("unauthenticated", 401)
    user = db.get(User, record.user_id)
    if not user or not user.active:
        fail("unauthenticated", 401)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), record.csrf):
            fail("csrf", 403)
    request.state.login_session = record
    return user
```

读这段时按顺序检查四件事：

1. Cookie 中拿到的是会话随机值，经过摘要后查 `LoginSession`，不是直接拿用户 ID 当凭据。
2. 会话必须存在且没过期；关联用户还必须处于 active 状态。
3. GET、HEAD、OPTIONS 以外的方法要求与该会话绑定的 `x-csrf-token`，用 `compare_digest` 比较。
4. 认证记录放到 `request.state` 供后续流程使用；前端无法通过额外 JSON 字段替换这个对象。

`app.py::boundary` 另外检查写请求 Origin。实际调试中，只有 Cookie 而缺 CSRF 头会失败；有 CSRF 头而 Origin 不在允许集合也会失败。浏览器登录路径、API 代理路径与 public origin 需要成套配置，不能删掉检查来“修好”403。

### 团队成员校验是另外一次判断

同一文件的 `membership` 原函数：

```python
def membership(db: Session, user: User, team_id: str, admin: bool = False) -> tuple[Team, Member]:
    team = db.get(Team, team_id)
    member = db.scalar(select(Member).where(Member.team_id == team_id, Member.user_id == user.id,
                                           Member.active.is_(True)))
    if not team or not team.active or not member:
        fail("team_unavailable", 403)
    if admin and not user.platform_admin and member.role != "admin":
        fail("forbidden", 403)
    return team, member
```

`Member` 同时匹配用户与团队，且必须 active；团队自身也必须 active。`admin=True` 再检查角色。随后针对具体 thread／file 仍需要资源授权，团队成员身份不应自动授予其他成员的所有资源。

如果把它简化为 `if user.platform_admin: pass`，会改变原本针对团队、成员生命周期和资源归属的规则。学习代码时应沿调用方追踪“团队检查”和“资源检查”各发生在哪一步。

## Agent 工具的能力边界

把模型输出当成不可信输入，工具服务器仍需校验参数、资源归属、路径、预算与审批状态。提示词“不要访问别人的文件”无法替代操作系统或服务端限制。

| 风险 | 工程处理 |
| --- | --- |
| SQL 注入 | SQLAlchemy 参数绑定；不用用户文本拼接 SQL 语句 |
| 命令注入 | 用参数列表调用固定程序，禁止把模型文本拼到 `shell=True` |
| 路径穿越 | 服务端生成标识；解析后验证位于允许根目录，处理符号链接竞态 |
| SSRF | 限定协议、域名、端口；校验 DNS 与重定向；禁止访问云元数据和内网管理地址，配置出口限制 |
| 提示注入 | 文档是数据；不能让文档改变工具授权、收件人、付款或密钥策略 |
| 资源耗尽 | 请求体、文件、并发数、排队长度、调用次数、tokens、执行时长和输出大小上限 |
| 凭据泄露 | 服务端按用户／工具绑定密钥，日志脱敏，不把无关密钥交给模型 |
| 文件上传攻击 | 类型与内容检查、大小配额、随机存储名、隔离解析、下载授权 |
| 重试副作用 | 使用业务幂等键；不确定是否提交成功时先查询外部任务状态 |

文件策略可参考 [OWASP 文件上传指南](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)，Agent 工具授权可参考 [OWASP AI Agent 安全指南](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)。

## 资源限制与错误分析

工具调用设置每次超时和整次 run 预算，控制并发和最大步骤数；执行子进程时管理整个进程组，先温和终止再强制结束。协程取消不等于外部计算停止，需要调用外部系统的取消 API，并记录取消结果。

Docker 的 CPU、内存、进程数和只读文件系统可以限制普通服务的资源，不能单独作为互不信任租户执行任意代码的安全边界。公共代码执行需要独立的执行身份、文件与网络隔离及经过验证的沙箱／虚拟机；不能挂载宿主 Docker socket 或个人主目录。Archeos 的执行策略入口见[源码阅读](../交付与实战/Archeos与ALKEMIE源码阅读.md)。

错误分析先按 `run_id` 定位：请求是否接收、是否入库、是否投递、worker 是否领取、哪次工具调用失败、错误是否可重试、外部副作用是否已发生。保存错误码、尝试次数和经脱敏的阶段信息，避免把整个提示词和凭据直接写入追踪。

Demo 实现用户归属、会话撤销、有限输入、执行期限与有限重试，只运行固定统计工具。它没有公共登录限流、完整租户配额、外部工具沙箱或入口总请求体限制；先补齐这些机制，再开放到公网。

## 用两个账号做可观察的权限实验

运行[请求案例脚本](../../../scripts/backend/run_agent_example.py)会在全新临时库创建 reader_a、reader_b，密码随机生成且不输出；它不会碰现有 Archeos／ALKEMIE 账号。A 创建会话和 run 后，B 请求同一 run 与历史消息，都应得到 404。

| 实验 | 不应出现的现象 | 正确证据 |
| --- | --- | --- |
| 无令牌读会话 | 返回任何会话 | 401 |
| B 读 A 的 run | 能看到状态或输出 | 404，和不存在资源一致 |
| B 向 A 的会话上传 | 生成附件记录 | 404，无新附件 |
| A 退出后复用旧令牌 | 仍能读历史 | 401 |
| 已连接 SSE 后撤销登录 | 永久继续输出 | 下一轮复查后结束订阅 |

逐资源校验应在服务器完成，隐藏按钮、不可猜 UUID 和前端路由守卫都不构成服务器授权。

### Demo 的摘要、到期与撤销

[security.py::authenticate](../../../examples/backend/agent-demo/demo/security.py) 在校验密码后生成 `secrets.token_urlsafe(32)`，数据库只存 digest；[main.py::logout](../../../examples/backend/agent-demo/demo/main.py) 删除该摘要记录。数据库里没有 JWT 签名密钥，因为此方案本来就是不透明服务端会话。

验证撤销时，必须重复使用同一旧凭据访问受保护接口；“退出响应为 204”只证明退出接口返回成功。长连接还要通过 `event_page` 再查登录是否存在和过期。

## 把 Agent 权限放在工具执行之前

假设模型请求 `read_file(path='../../another-user/key')`，服务端需要先从当前用户／run 的授权上下文解析允许根目录，再解析资源标识并核对归属。工具参数只描述希望做什么，不能自己带 `as_admin=true` 改变授权身份。

| 预算 | 计量位置 | 失败时保存什么 |
| --- | --- | --- |
| 请求体与文件字节 | 代理／ASGI 接收层、解析后文件检查 | 413、来源与计数，不存整文件到日志 |
| 工具并发数 | 实际执行工具之前的信号量／执行器 | 排队时间、工具名 |
| 单次工具和 run 时间 | 工具客户端与整体执行上下文 | deadline、timeout 类别 |
| 调用次数和 tokens | 每次调用前检查、调用后核算 | 已用／上限、停止原因 |
| 进程 CPU／内存／PID | 操作系统或受限执行节点 | 退出码、资源终止原因 |

`asyncio.Semaphore` 只约束一个进程中的相应调用路径，API 启动 4 个进程后不能据此宣称全系统仍只有 2 个并发。全局或按用户的配额需要数据库／Redis 原子计数，或集中调度器执行。输入超时参数也必须和服务端上限取最小值，不能让用户传 `timeout=0` 表示无限执行。

真实接入前给每个工具设计允许动作、输入模型、资源范围、出站域名、超时、最大输出和副作用幂等策略，再把这些检查绑定到执行入口。这样错误分析才能指出具体哪条规则拒绝了动作。
