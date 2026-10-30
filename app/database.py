"""Подключение к базе данных через асинхронную SQLAlchemy."""

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./recipes.db")

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI-зависимость: отдельная сессия БД на каждый запрос."""
    async with async_session() as session:
        yield session
