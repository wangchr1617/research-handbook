"""读取 JSON 并发调用固定 HTTP 工具；需 Demo 的 Python 3.12 依赖。

用法：python scripts/backend/并发调用HTTP工具.py inputs/backend/tools-normal.json
--base-url 为操作者指定的服务地址；输入文件只允许固定工具路径，所有期限单位为秒。
"""
import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Call(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=40)
    path: Literal["/tools/word-count", "/tools/character-count", "/tools/unavailable"]
    delay_seconds: float = Field(default=0, ge=0, le=2)
    timeout_seconds: float = Field(default=1, gt=0, le=10)


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=100000)
    calls: list[Call] = Field(min_length=1, max_length=20)
    total_timeout_seconds: float = Field(default=3, gt=0, le=30)
    max_concurrency: int = Field(default=2, ge=1, le=8, strict=True)

    @model_validator(mode="after")
    def unique_names(self):
        if len({item.name for item in self.calls}) != len(self.calls):
            raise ValueError("tool names must be unique")
        return self


async def call_one(client, call, text, semaphore):
    start = time.monotonic()
    try:
        async with asyncio.timeout(call.timeout_seconds):
            async with semaphore:
                response = await client.post(call.path, json={"text": text, "delay_seconds": call.delay_seconds})
                response.raise_for_status()
                result = {"name": call.name, "status": "ok", "result": response.json()}
    except (TimeoutError, httpx.TimeoutException):
        result = {"name": call.name, "status": "timeout"}
    except httpx.HTTPStatusError as exc:
        result = {"name": call.name, "status": "http_error", "http_status": exc.response.status_code}
    except httpx.RequestError:
        result = {"name": call.name, "status": "network_error"}
    except asyncio.CancelledError:
        raise
    result["elapsed_ms"] = round((time.monotonic() - start) * 1000, 1)
    return result


async def run_plan(plan, base_url="http://127.0.0.1:8001", transport=None):
    semaphore = asyncio.Semaphore(plan.max_concurrency)
    start = time.monotonic()
    # 网络各阶段的空闲期限与整次工具期限分开设置；trust_env=False 避免本机代理干扰。
    timeout = httpx.Timeout(connect=1, read=3, write=1, pool=1)
    limits = httpx.Limits(max_connections=plan.max_concurrency, max_keepalive_connections=plan.max_concurrency)
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout, limits=limits,
                                 transport=transport, trust_env=False) as client:
        try:
            async with asyncio.timeout(plan.total_timeout_seconds):
                async with asyncio.TaskGroup() as group:
                    tasks = [group.create_task(call_one(client, item, plan.text, semaphore)) for item in plan.calls]
        except TimeoutError:
            # TaskGroup 已取消并等待子任务；外层超时不冒充一组完整的局部结果。
            return {"status": "deadline_exceeded", "elapsed_ms": round((time.monotonic() - start) * 1000, 1)}
    return {"status": "completed", "elapsed_ms": round((time.monotonic() - start) * 1000, 1),
            "results": [task.result() for task in tasks]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="工具调用 JSON 文件")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="由操作者指定的工具服务根地址")
    args = parser.parse_args()
    plan = Plan.model_validate_json(args.input.read_text())
    result = asyncio.run(run_plan(plan, args.base_url))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
