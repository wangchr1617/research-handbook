# HTTP 接口与参数校验

**适用环境：通用；代码为 Python 3.12、FastAPI、Pydantic 2。命令在本机终端执行。**

## 从资源和操作开始

HTTP 请求由方法、路径、请求头和可选请求体组成，响应包含状态码、响应头和响应体。把“会话”“消息”“执行任务”建模为资源，比为每个页面设计一个随意命名的接口更容易扩展。

| 方法 | 常见用途 | Agent 示例 | 基本语义 |
| --- | --- | --- | --- |
| GET | 读取资源或列表 | `GET /api/conversations` | 安全、幂等，不触发计费模型调用或写任务 |
| POST | 创建资源或执行命令 | `POST /api/conversations/{id}/runs` | 通常不幂等；需要时显式设计幂等键 |
| PUT | 用完整表示替换资源 | `PUT /api/agents/{id}/config` | 幂等；明确省略字段的含义 |
| PATCH | 部分修改 | `PATCH /api/conversations/{id}` | 是否幂等取决于补丁操作；“设为某值”与“加一”不同 |
| DELETE | 删除资源 | `DELETE /api/files/{id}` | 幂等指最终效果一致，重复请求的状态码可以不同 |
| HEAD | 只取响应头 | 检查附件元信息 | 无响应体 |
| OPTIONS | 查询通信选项 | 浏览器 CORS 预检 | 通常由框架／代理处理 |

安全方法的日志、计数等附带操作不等于业务写入。接口语义见 [MDN HTTP 方法](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods)。

执行任务通常返回 `202 Accepted` 与 `run_id`，表示已接收；客户端用另一个 GET 接口查询结果。同步创建会话可返回 `201 Created`，读取成功用 `200`，无响应体的成功操作可用 `204`。

| 状态码 | 典型含义 |
| --- | --- |
| 400 | 业务上无法理解的请求 |
| 401 | 缺少或失效的登录凭据 |
| 403 | 已认证，但没有所需权限 |
| 404 | 资源不存在；也可用于隐藏无权查看的资源 |
| 409 | 版本冲突、重复资源、幂等键对应不同内容 |
| 413 / 415 | 内容过大／不支持的媒体类型 |
| 422 | FastAPI 的输入校验失败 |
| 429 | 请求或预算超过限额 |
| 500 / 503 | 内部错误／依赖或服务暂不可用 |

## 参数从哪里来

- 路径参数标识资源，例如 `/conversations/{conversation_id}`。
- 查询参数控制筛选、排序和分页，例如 `?before=120&limit=50`。
- JSON 请求体表达结构化输入，声明 `Content-Type: application/json`。
- 请求头携带认证、追踪与协议元信息；不要把密码或令牌放 URL。
- 文件通常使用 `multipart/form-data`。同一次 multipart 请求里的附加字段使用 `Form`；不能同时把整个请求体当作普通 JSON 解码。

FastAPI 可根据类型注解区分这些位置，参考[请求体](https://fastapi.tiangolo.com/tutorial/body/)与[文件上传](https://fastapi.tiangolo.com/tutorial/request-files/)。

## 用 Pydantic 约束输入

下面是参照 Archeos `schemas.py` 的输入模型风格写成的独立教学片段：

```python
from typing import Annotated
from fastapi import FastAPI, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

app = FastAPI()

class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=2000)
    timeout_seconds: int = Field(default=10, ge=1, le=20, strict=True)

    @field_validator("prompt")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("prompt must contain text")
        return value

@app.post("/api/validate-run")
def validate_run(body: RunInput):
    return body.model_dump()

@app.get("/api/page")
def page(limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return {"limit": limit}
```

保存为 `main.py`，在已安装 FastAPI、Uvicorn 的隔离环境中执行 `uvicorn main:app --reload`，打开 `/docs`。传入 `{"prompt":"分析材料","timeout_seconds":5}` 应成功；超出范围、未知字段，或把严格整数字段写成字符串 `"5"`，应得到 `422`。查询参数原本来自字符串，框架可按 `Query` 的声明转换；不要对所有位置机械套用相同严格策略。

Pydantic 2 常用入口是 `model_validate()`、`model_dump()`、`field_validator`，并通过 `ConfigDict` 配置。默认允许的类型转换与严格校验不同，见 [Pydantic 模型](https://docs.pydantic.dev/latest/concepts/models/)和[严格模式](https://docs.pydantic.dev/latest/concepts/strict_mode/)。参数格式正确之后，还需要检查用户权限、资源归属与数据库约束。

## 拆开看一条真实的任务请求

[run-normal.json](../../../inputs/backend/run-normal.json) 是可直接提交给 Demo 的输入：

```json
{
  "prompt": "请统计这份研究笔记的文本。",
  "client_key": "backend-normal-001",
  "timeout_seconds": 5,
  "mode": "normal"
}
```

假设登录令牌保存在变量 `token`，会话 ID 是 `conversation_id`，HTTP 报文的关键部分如下。`${...}` 表示需要替换的值，不是服务端自动识别的语法：

```http
POST /api/conversations/${conversation_id}/runs HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer ${token}
Content-Type: application/json

{"prompt":"请统计这份研究笔记的文本。","client_key":"backend-normal-001","timeout_seconds":5,"mode":"normal"}
```

请求头和请求体之间有一个空行。`conversation_id` 选定资源，Bearer 头标识当前用户，JSON 表达执行意图。服务端只从认证结果取得用户身份，JSON 中没有让客户端任意指定所有者的 `user_id`。

对应的真实输入类位于 [demo/schemas.py::RunInput](../../../examples/backend/agent-demo/demo/schemas.py)：

```python
class RunInput(Input):
    prompt: str = Field(min_length=1, max_length=2000)
    client_key: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,64}$")
    attachment_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    timeout_seconds: int = Field(default=10, ge=1, le=20, strict=True)
    mode: Literal["normal", "retry_once", "slow", "fail"] = "normal"
```

这些字段分别约束：`prompt` 最多 2,000 字符；`client_key` 限定字符集与长度；附件 ID 可以省略，提供时须为 32 位十六进制标识；期限必须是 1—20 秒的整数；mode 只接受四个允许值。该类继承的 `Input` 设置 `extra="forbid"`，所以拼错字段不会静默失效。`min_length=1` 检查字符长度，仍会接受全空格；若业务禁止空白文本，应增加语义 validator，而不是误以为长度约束已经处理了它。

### 422 到底在哪一步产生

[run-invalid.json](../../../inputs/backend/run-invalid.json) 把 `timeout_seconds` 写成字符串，并加入未知字段。Demo 校验处理器的响应形状为：

```json
{
  "code": "validation",
  "request_id": "每次请求生成的追踪标识",
  "fields": [["body", "timeout_seconds"], ["body", "unexpected_option"]]
}
```

这次请求不会进入 `submit()` 的函数体，因此不应创建 run 或用户消息。这是 Demo 自定义的错误结构；FastAPI 默认结构通常有 `detail`，不能把两种格式混在同一客户端处理函数中。

不启动服务也能先练模型校验。在 Demo 目录及虚拟环境中执行：

```bash
python - <<'PYCODE'
from pathlib import Path
from pydantic import ValidationError
from demo.schemas import RunInput
inputs = Path('../../../inputs/backend')
for name in ('run-normal.json', 'run-invalid.json'):
    try:
        body = RunInput.model_validate_json((inputs / name).read_text())
        print(name, 'accepted', body.timeout_seconds)
    except ValidationError as exc:
        print(name, [(e['loc'], e['type']) for e in exc.errors()])
PYCODE
```

这只检查输入类，不检查身份、会话是否存在或附件归属。完整请求练习见 [Agent 请求与恢复实操](../../../examples/backend/agent-demo/请求与恢复实操.md)。

### 为什么输入模型和响应模型不同

Archeos 的真实登录输入使用 email，Demo 使用 username，不能互相照搬请求文件。[Archeos schemas.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/archeos/schemas.py) 中的模型是：

```python
class Credentials(Input):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def email_format(cls, value):
        value = value.strip().lower()
        if "@" not in value or any(c.isspace() for c in value):
            raise ValueError("Invalid email")
        return value
```

邮箱在进入业务前被去首尾空白并转为小写；这个轻量检查不等于完整邮件地址验证或邮箱所有权验证。登录密码允许已有用户输入较短旧密码，创建／更改密码时另有更严格策略，两个流程不能混为一谈。

响应中的 `UserView` 只返回允许公开的字段；哈希、令牌加密字段和内部权限对象不能因为“都是 ORM 字段”就一起序列化。为接口声明 `response_model` 还能让 OpenAPI 表达响应约定，并在服务端发现输出不符合模型的问题。

## 设计可长期使用的接口

响应模型与输入模型分开：不要直接返回含 `password_hash` 的 ORM 对象。返回稳定的错误码和 `request_id`，把堆栈留在服务日志。时间统一使用带时区的 UTC 时间，或明确约定 Unix 秒；文件大小注明字节，超时注明秒。

列表必须有上限和稳定排序。消息可以按递增 `id` 做游标：先取 `id < before` 的最新 50 条，再反转为时间正序。按时间分页时应同时携带 `(created_at, id)`，避免时间相同的记录被跳过。Demo 会话列表使用简化的时间游标，完整分页应升级为双字段游标。

客户端重试 POST 时复用同一个 `client_key`。服务端在 `(conversation_id, client_key)` 上加唯一约束，并核对输入内容：相同键、相同输入返回原任务；相同键、不同输入返回 `409`。前端按钮禁用只能减少误点，数据库约束才能处理真正的并发竞争。

## 文件上传的检查

配套 Demo 的 `demo/main.py::upload` 接收 `UploadFile`，验证会话归属，只允许 `.txt`、`.md` 和 UTF-8 文本，最多读取 65,537 字节后判定是否超过 64 KiB。小附件存数据库，原始文件名只用于展示。

更大的文件使用对象存储和服务端生成的文件标识；下载也需要授权。扩展名与 `Content-Type` 都不能单独证明内容安全。入口代理还应限制完整请求体，避免 multipart 解析阶段先耗尽磁盘或内存；压缩包需要限制展开大小、文件数量和路径。具体策略见[权限与安全](用户认证权限与Agent安全.md)。

## 顺着上传函数检查每一道边界

下面是 [Demo upload](../../../examples/backend/agent-demo/demo/main.py) 的完整实现；它接收的表单字段名是 `file`：

```python
@app.post("/api/conversations/{conversation_id}/files", status_code=201)
def upload(conversation_id: str, user: CurrentUser, file: Annotated[UploadFile, File()]):
    with session() as db:
        own_conversation(db, conversation_id, user)
        # 文件名仅用于展示，不参与磁盘路径。只接收小型 UTF-8 文本。
        name = Path((file.filename or "").replace("\\", "/")).name
        if Path(name).suffix.lower() not in {".txt", ".md"} or len(name) > 120:
            raise HTTPException(415, "text_file_required")
        data = file.file.read(settings().upload_bytes + 1)
        if len(data) > settings().upload_bytes:
            raise HTTPException(413, "file_too_large")
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(415, "utf8_required") from None
        if "\x00" in content:
            raise HTTPException(415, "text_file_required")
        item = Attachment(conversation_id=conversation_id, filename=name, content=content)
        db.add(item)
        db.commit()
        return {"id": item.id, "filename": item.filename, "bytes": len(data)}
```

先校验所属会话，再检查展示文件名；`read(limit + 1)` 可以区分“刚好到上限”和“已经超限”，不需要无限制读取。UTF-8 解码和 NUL 检查拒绝部分非文本内容，但不保证将来的 PDF／Office 解析器安全。附件在数据库中与会话绑定，提交任务时还会再次验证附件属于当前会话。

| 具体输入 | 结果 | 由哪一步决定 |
| --- | --- | --- |
| `研究笔记样例.md`，226 字节 UTF-8 | 201，返回附件 ID | 类型、大小、内容均通过 |
| 同样内容改名 `example.py` | 415 | 后缀不在允许集合 |
| `.txt` 内含无法 UTF-8 解码的字节 | 415 | 解码失败 |
| `.txt` 大于 65,536 字节 | 413 | 多读 1 字节后判超限 |
| 用户 B 向 A 的会话上传 | 404 | 先执行资源归属校验 |

表中的 226 字节对应仓库原始样例；编辑器改变换行或内容后大小会改变。`Content-Length` 快速检查和上传函数的文件大小检查分处不同阶段；multipart 预解析前的总流量限制仍应由入口代理或 ASGI 接收层实施。
