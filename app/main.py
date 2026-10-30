"""
API кулинарной книги на FastAPI и асинхронной SQLAlchemy.

Запуск (из папки homework):
    uvicorn app.main:app --reload
Документация: http://127.0.0.1:8000/docs (Swagger UI) и http://127.0.0.1:8000/redoc
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, engine, get_session
from .models import Ingredient, Recipe
from .schemas import ErrorResponse, RecipeCreate, RecipeDetail, RecipeListItem
from .seed import seed_recipes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """При старте создаём таблицы и заполняем пустую базу примерами рецептов."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await seed_recipes()
    yield
    await engine.dispose()


DESCRIPTION = """
Бэкенд кулинарной книги.

## Экраны

* **Список рецептов** — `GET /recipes`.
  Таблица: название, количество просмотров, время приготовления.
  Сортировка: сначала самые просматриваемые;
  при равном числе просмотров — сначала те, что готовятся быстрее.
* **Детальный рецепт** — `GET /recipes/{recipe_id}`.
  Название, время приготовления, ингредиенты, описание.
  Каждый запрос к этому эндпоинту считается просмотром и увеличивает счётчик `views` на 1.

## Создание рецепта

`POST /recipes` — новый рецепт с ингредиентами, счётчик просмотров начинается с 0.

## Ошибки

* `404` — рецепта с таким `recipe_id` нет: `{"detail": "..."}`;
* `422` — тело запроса или параметр пути не прошли валидацию;
  в ответе FastAPI указано, какое поле и почему.
"""

app = FastAPI(
    title="Кулинарная книга",
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "recipes", "description": "Рецепты: список, детальная информация, создание"}
    ],
)


@app.get(
    "/recipes",
    response_model=List[RecipeListItem],
    tags=["recipes"],
    summary="Список всех рецептов",
    description=(
        "Все рецепты для таблицы на первом экране. "
        "Отсортированы по убыванию количества просмотров, "
        "при равенстве просмотров — по возрастанию времени приготовления. "
        "Просмотры этот запрос не увеличивает."
    ),
)
async def get_recipes(session: AsyncSession = Depends(get_session)) -> List[Recipe]:
    result = await session.scalars(
        select(Recipe).order_by(Recipe.views.desc(), Recipe.cooking_time.asc(), Recipe.id.asc())
    )
    return list(result)


@app.get(
    "/recipes/{recipe_id}",
    response_model=RecipeDetail,
    tags=["recipes"],
    summary="Детальная информация о рецепте",
    description=(
        "Возвращает рецепт с ингредиентами и описанием. "
        "Каждый вызов увеличивает счётчик просмотров на 1."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Рецепт не найден"}
    },
)
async def get_recipe(
    recipe_id: int = Path(..., gt=0, description="Идентификатор рецепта", examples=[1]),
    session: AsyncSession = Depends(get_session),
) -> Recipe:
    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipe with id {recipe_id} not found"
    )
    # Атомарный UPDATE на стороне БД: одновременные просмотры не потеряются.
    # RETURNING сообщает, нашлась ли строка, без отдельного SELECT.
    updated_id: Optional[int] = await session.scalar(
        update(Recipe)
        .where(Recipe.id == recipe_id)
        .values(views=Recipe.views + 1)
        .returning(Recipe.id)
    )
    if updated_id is None:
        raise not_found
    await session.commit()

    recipe: Optional[Recipe] = await session.get(Recipe, recipe_id, populate_existing=True)
    if recipe is None:  # рецепт удалили между UPDATE и SELECT
        raise not_found
    return recipe


@app.post(
    "/recipes",
    response_model=RecipeDetail,
    status_code=status.HTTP_201_CREATED,
    tags=["recipes"],
    summary="Создать рецепт",
    description="Создаёт рецепт вместе с ингредиентами и возвращает его полное описание.",
)
async def create_recipe(
    recipe_in: RecipeCreate, session: AsyncSession = Depends(get_session)
) -> Recipe:
    recipe = Recipe(
        title=recipe_in.title,
        cooking_time=recipe_in.cooking_time,
        description=recipe_in.description,
        views=0,
        ingredients=[
            Ingredient(name=item.name, amount=item.amount) for item in recipe_in.ingredients
        ],
    )
    session.add(recipe)
    await session.commit()
    return recipe
