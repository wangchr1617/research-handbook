"""数据库模型；python -m demo.manage init 初始化空练习库。"""
import time
import uuid
from functools import lru_cache
from pathlib import Path

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


def uid():
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)


class Login(Base):
    __tablename__ = "logins"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[float]


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[float] = mapped_column(default=time.time)


class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    filename: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("conversation_id", "client_key"),
        Index("ix_run_dispatch", "status", "next_at"),
    )
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    client_key: Mapped[str] = mapped_column(String(64))
    prompt: Mapped[str] = mapped_column(Text)
    attachment_id: Mapped[str | None] = mapped_column(ForeignKey("attachments.id"))
    mode: Mapped[str] = mapped_column(String(16), default="normal")
    status: Mapped[str] = mapped_column(String(16), default="queued")
    attempt: Mapped[int] = mapped_column(default=0)
    timeout_seconds: Mapped[int] = mapped_column(default=10)
    lease: Mapped[str | None] = mapped_column(String(32))
    deadline: Mapped[float | None]
    next_at: Mapped[float] = mapped_column(default=time.time)
    created_at: Mapped[float] = mapped_column(default=time.time)
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    error_code: Mapped[str | None] = mapped_column(String(40))
    request_id: Mapped[str] = mapped_column(String(32))


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("run_id", "role"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[float] = mapped_column(default=time.time)


class RunEvent(Base):
    __tablename__ = "run_events"
    __table_args__ = (Index("ix_event_run_cursor", "run_id", "id"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    kind: Mapped[str] = mapped_column(String(16))
    data: Mapped[str] = mapped_column(Text)
    created_at: Mapped[float] = mapped_column(default=time.time)


@lru_cache
def engine():
    url = settings().database_url
    if url.startswith("sqlite"):
        Path("data").mkdir(exist_ok=True)
    db_engine = create_engine(url, pool_pre_ping=True, connect_args={"check_same_thread": False}
                              if url.startswith("sqlite") else {})
    if url.startswith("sqlite"):
        @event.listens_for(db_engine, "connect")
        def sqlite_options(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA busy_timeout=5000")
    return db_engine


def session():
    return sessionmaker(engine(), expire_on_commit=False)()
