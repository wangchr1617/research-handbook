# 后端工程练习脚本

**适用环境：Python 3.12；Linux、macOS 或 Windows WSL。安装 Agent Demo 的依赖锁文件，使用同一隔离环境。**

所有命令从仓库根目录运行：

```bash
python scripts/backend/运行Agent案例.py --output-dir /tmp/agent-backend-lab
python scripts/backend/并发调用HTTP工具.py inputs/backend/tools-normal.json
```

| 脚本 | 输入与输出 | 适用边界 |
| --- | --- | --- |
| [运行Agent案例.py](运行Agent案例.py) | 读取 `inputs/backend`，在全新目录生成 SQLite、报告和 SSE 文件 | 使用真实 API 代码和直接 worker 执行函数；不使用网络 broker |
| [并发调用HTTP工具.py](并发调用HTTP工具.py) | 读取工具调用 JSON，输出每项结果与耗时 | 需先启动本机 HTTP 工具服务；支持 `--base-url` |

`运行Agent案例.py` 的输出目录必须不存在，避免覆盖任何已有数据库。退出后随机测试密码不保留在脚本输出中；练习库仅含新建教学账号和公开样例文本，仍不应当作正式用户库。

运行工具服务、查看 SQL、重试与故障练习见[请求与恢复实操](../../examples/backend/agent-demo/请求与恢复实操.md)。
