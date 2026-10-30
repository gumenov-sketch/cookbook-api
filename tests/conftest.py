import os
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator, Iterator

import pytest

# База для старта приложения (lifespan) — временная, чтобы тесты не трогали recipes.db.
_TMP_DIR = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{Path(_TMP_DIR) / 'startup.db'}"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    """Клиент, у которого каждый тест работает с собственной пустой базой."""
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    test_sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)

    async def create_tables() -> None:
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with test_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        portal = test_client.portal
        assert portal is not None, "TestClient portal is available inside the context manager"
        portal.call(create_tables)
        yield test_client
        portal.call(test_engine.dispose)
    app.dependency_overrides.clear()


@pytest.fixture()
def recipe_payload() -> dict[str, Any]:
    return {
        "title": "Блины",
        "cooking_time": 40,
        "ingredients": [
            {"name": "Мука", "amount": "200 г"},
            {"name": "Молоко", "amount": "500 мл"},
        ],
        "description": "Смешать и пожарить.",
    }
