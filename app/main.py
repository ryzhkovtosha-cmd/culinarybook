from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание таблиц при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Очистка (опционально)
    await engine.dispose()


app = FastAPI(
    title="Кулинарная книга API",
    description="API для управления рецептами. "
    "Позволяет просматривать список рецептов, "
    "получать детальную информацию "
    "(с автоувеличением счётчика просмотров) "
    "и добавлять новые рецепты.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post(
    "/recipes",
    response_model=schemas.RecipeDetail,
    status_code=201,
    summary="Создать новый рецепт",
)
async def create_recipe(
    recipe: schemas.RecipeCreate, db: AsyncSession = Depends(get_db)
):
    """
    Добавляет новый рецепт в базу данных.
    - **name**: название блюда
    - **cooking_time**: время приготовления в минутах
    - **ingredients**: список ингредиентов
    - **description**: текстовое описание
    """
    new_recipe = await crud.create_recipe(db, recipe)
    return new_recipe


@app.get(
    "/recipes",
    response_model=list[schemas.RecipeListItem],
    summary="Получить список всех рецептов",
)
async def list_recipes(db: AsyncSession = Depends(get_db)):
    """
    Возвращает список всех рецептов, отсортированный по убыванию просмотров,
    а при равном количестве – по возрастанию времени готовки.
    Каждый элемент содержит:
    - название
    - количество просмотров
    - время готовки (минуты)
    """
    recipes = await crud.get_recipes_list(db)
    return recipes


@app.get(
    "/recipes/{recipe_id}",
    response_model=schemas.RecipeDetail,
    summary="Получить детальную информацию о рецепте",
)
async def recipe_detail(recipe_id: int, db: AsyncSession = Depends(get_db)):
    """
    Возвращает полную информацию о рецепте по его ID.
    При каждом вызове счётчик просмотров увеличивается на 1.
    - **recipe_id**: идентификатор рецепта
    """
    recipe = await crud.get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    updated_recipe = await crud.increment_views(db, recipe_id)
    return updated_recipe
