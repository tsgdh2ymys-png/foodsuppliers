"""Слой данных.

По умолчанию — SQLite (ноль конфигурации, файл едет вместе с проектом).
Чтобы переехать на PostgreSQL в проде, достаточно задать переменную окружения
DATABASE_URL (например, postgresql+psycopg://user:pass@host/db) — код менять не нужно.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'suppliers.db')}",
)

# check_same_thread нужен только SQLite при работе с несколькими потоками (uvicorn).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI-зависимость: одна сессия на запрос."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
