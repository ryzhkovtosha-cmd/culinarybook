import os
import sys
from typing import AsyncGenerator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.main import app, get_db

# Тестовая БД – in-memory SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_recipe():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "name": "Борщ",
            "cooking_time": 90,
            "ingredients": ["свекла", "капуста", "картофель", "мясо"],
            "description": "Наваристый украинский борщ",
        }
        response = await ac.post("/recipes", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Борщ"
        assert data["views"] == 0
        assert "id" in data


@pytest.mark.asyncio
async def test_list_recipes_sorting():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r1 = {
            "name": "Популярный",
            "cooking_time": 30,
            "ingredients": ["a"],
            "description": "desc1",
        }
        r2 = {
            "name": "С быстрым временем",
            "cooking_time": 10,
            "ingredients": ["b"],
            "description": "desc2",
        }
        await ac.post("/recipes", json=r1)
        await ac.post("/recipes", json=r2)

        await ac.get("/recipes/1")
        await ac.get("/recipes/1")

        response = await ac.get("/recipes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Популярный"
        assert data[0]["views"] == 2
        assert data[1]["name"] == "С быстрым временем"
        assert data[1]["views"] == 0


@pytest.mark.asyncio
async def test_detail_increments_views():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        payload = {
            "name": "Салат",
            "cooking_time": 15,
            "ingredients": ["огурцы", "помидоры"],
            "description": "лёгкий салат",
        }
        post_resp = await ac.post("/recipes", json=payload)
        recipe_id = post_resp.json()["id"]

        resp1 = await ac.get(f"/recipes/{recipe_id}")
        assert resp1.status_code == 200
        assert resp1.json()["views"] == 1

        resp2 = await ac.get(f"/recipes/{recipe_id}")
        assert resp2.status_code == 200
        assert resp2.json()["views"] == 2

        resp404 = await ac.get("/recipes/999")
        assert resp404.status_code == 404
