"""本机 HTTP 工具：uvicorn demo.tool_api:app --host 127.0.0.1 --port 8001。

延时参数以秒计，仅用于观察并发与期限；固定文本工具不执行用户代码。
"""
import asyncio

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="本机 HTTP 工具练习")


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=100000)
    delay_seconds: float = Field(default=0, ge=0, le=2)


@app.post("/tools/word-count")
async def word_count(body: ToolInput):
    await asyncio.sleep(body.delay_seconds)
    return {"words": len(body.text.split())}


@app.post("/tools/character-count")
async def character_count(body: ToolInput):
    await asyncio.sleep(body.delay_seconds)
    return {"characters": len(body.text)}


@app.post("/tools/unavailable")
async def unavailable(body: ToolInput):
    await asyncio.sleep(body.delay_seconds)
    raise HTTPException(503, "controlled_tool_unavailable")
