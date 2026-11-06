"""请求模型限定类型、长度和允许字段，资源归属在 service 层检查。"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Credentials(Input):
    username: str = Field(pattern=r"^[a-zA-Z0-9_-]{3,40}$")
    password: str = Field(min_length=12, max_length=128)


class ConversationInput(Input):
    title: str = Field(min_length=1, max_length=80)


class RunInput(Input):
    prompt: str = Field(min_length=1, max_length=2000)
    client_key: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,64}$")
    attachment_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    timeout_seconds: int = Field(default=10, ge=1, le=20, strict=True)
    mode: Literal["normal", "retry_once", "slow", "fail"] = "normal"
