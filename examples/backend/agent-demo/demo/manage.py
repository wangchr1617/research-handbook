"""管理命令：python -m demo.manage init|user|dispatch；只操作本 Demo 配置的数据库。"""
import argparse
import getpass
import logging
import time

from sqlalchemy import select

from .db import Base, User, engine, session
from .jobs import dispatch_once
from .schemas import Credentials
from .security import passwords


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "user", "dispatch"])
    parser.add_argument("--username", default="student", help="创建本地练习账号的用户名")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command == "init":
        Base.metadata.create_all(engine())
        print("空库结构已准备；已有表不变，结构升级应使用迁移。")
    elif args.command == "user":
        password = getpass.getpass("练习账号密码（至少 12 字符）：")
        confirm = getpass.getpass("再次输入：")
        if password != confirm:
            raise SystemExit("两次密码不同")
        body = Credentials(username=args.username, password=password)
        with session() as db:
            if db.scalar(select(User.id).where(User.username == body.username)):
                raise SystemExit("账号已存在；本命令不覆盖密码")
            db.add(User(username=body.username, password_hash=passwords.hash(body.password)))
            db.commit()
    else:
        from .worker import enqueue
        try:
            while True:
                dispatch_once(enqueue)
                time.sleep(5)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
