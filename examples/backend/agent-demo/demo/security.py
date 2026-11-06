"""Argon2 密码哈希和短期不透明 Bearer 会话；令牌只保存摘要。"""
import hashlib
import secrets
import time
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from .config import settings
from .db import Conversation, Login, User, session

passwords = PasswordHasher()
dummy_hash = passwords.hash(secrets.token_urlsafe(24))
bearer = HTTPBearer(auto_error=False)


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def authenticate(username, password):
    with session() as db:
        user = db.scalar(select(User).where(User.username == username))
        try:
            passwords.verify(user.password_hash if user else dummy_hash, password)
        except VerificationError:
            raise HTTPException(401, "invalid_credentials") from None
        if user is None:
            raise HTTPException(401, "invalid_credentials")
        token = secrets.token_urlsafe(32)
        db.add(Login(token_hash=digest(token), user_id=user.id,
                     expires_at=time.time() + settings().session_seconds))
        db.commit()
        return {"access_token": token, "token_type": "bearer"}


def user_id(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None:
        raise HTTPException(401, "unauthenticated", headers={"WWW-Authenticate": "Bearer"})
    with session() as db:
        login = db.get(Login, digest(credentials.credentials))
        if not login or login.expires_at <= time.time() or not db.get(User, login.user_id):
            raise HTTPException(401, "unauthenticated")
        return login.user_id


CurrentUser = Annotated[str, Depends(user_id)]


def own_conversation(db, conversation_id, owner):
    item = db.scalar(select(Conversation).where(Conversation.id == conversation_id,
                                               Conversation.user_id == owner))
    if item is None:
        raise HTTPException(404, "not_found")
    return item
