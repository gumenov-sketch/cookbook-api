"""Примеры рецептов для пустой базы, чтобы фронтенду было что показать сразу."""

from dataclasses import dataclass

from sqlalchemy import func, select

from .database import async_session
from .models import Ingredient, Recipe


@dataclass(frozen=True)
class SampleRecipe:
    title: str
    cooking_time: int
    description: str
    ingredients: tuple[tuple[str, str], ...]


SAMPLE_RECIPES: tuple[SampleRecipe, ...] = (
    SampleRecipe(
        title="Блины",
        cooking_time=40,
        description=(
            "Смешать яйца с сахаром и солью, влить молоко, постепенно добавить муку. "
            "Дать тесту постоять 15 минут и жарить на разогретой сковороде с двух сторон."
        ),
        ingredients=(
            ("Мука", "200 г"),
            ("Молоко", "500 мл"),
            ("Яйца", "2 шт."),
            ("Сахар", "1 ст. л."),
            ("Соль", "щепотка"),
            ("Растительное масло", "2 ст. л."),
        ),
    ),
    SampleRecipe(
        title="Омлет",
        cooking_time=10,
        description=(
            "Взбить яйца с молоком и солью, вылить на сковороду с маслом, "
            "готовить под крышкой 5 минут."
        ),
        ingredients=(
            ("Яйца", "3 шт."),
            ("Молоко", "50 мл"),
            ("Сливочное масло", "10 г"),
            ("Соль", "по вкусу"),
        ),
    ),
    SampleRecipe(
        title="Греческий салат",
        cooking_time=15,
        description=(
            "Нарезать овощи и сыр крупными кубиками, добавить маслины, "
            "заправить маслом и орегано."
        ),
        ingredients=(
            ("Помидоры", "2 шт."),
            ("Огурец", "1 шт."),
            ("Сладкий перец", "1 шт."),
            ("Фета", "100 г"),
            ("Маслины", "50 г"),
            ("Оливковое масло", "2 ст. л."),
        ),
    ),
)


async def seed_recipes() -> None:
    async with async_session() as session:
        if await session.scalar(select(func.count()).select_from(Recipe)):
            return
        for sample in SAMPLE_RECIPES:
            session.add(
                Recipe(
                    title=sample.title,
                    cooking_time=sample.cooking_time,
                    description=sample.description,
                    views=0,
                    ingredients=[
                        Ingredient(name=name, amount=amount) for name, amount in sample.ingredients
                    ],
                )
            )
        await session.commit()
