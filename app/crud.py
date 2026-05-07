from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Recipe
from app.schemas import RecipeCreate

async def create_recipe(db: AsyncSession, recipe: RecipeCreate) -> Recipe:
    db_recipe = Recipe(**recipe.model_dump())
    db.add(db_recipe)
    await db.commit()
    await db.refresh(db_recipe)
    return db_recipe

async def get_recipes_list(db: AsyncSession):
    stmt = select(Recipe).order_by(Recipe.views.desc(), Recipe.cooking_time.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_recipe_by_id(db: AsyncSession, recipe_id: int):
    stmt = select(Recipe).where(Recipe.id == recipe_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def increment_views(db: AsyncSession, recipe_id: int):
    stmt = (
        update(Recipe)
        .where(Recipe.id == recipe_id)
        .values(views=Recipe.views + 1)
        .returning(Recipe)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()