"""Pydantic-схемы запросов и ответов. Описания полей попадают в документацию /docs."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class IngredientBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Название ингредиента", examples=["Мука"]
    )
    amount: str = Field(
        "",
        max_length=50,
        description="Количество в свободной форме; может быть пустым",
        examples=["200 г"],
    )


class IngredientIn(IngredientBase):
    """Ингредиент в запросе на создание рецепта."""


class IngredientOut(IngredientBase):
    """Ингредиент в ответе."""

    model_config = ConfigDict(from_attributes=True)


class RecipeCreate(BaseModel):
    """Тело запроса POST /recipes — новый рецепт."""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Название блюда", examples=["Блины"]
    )
    cooking_time: int = Field(
        ...,
        gt=0,
        le=10_000,
        description="Время приготовления в минутах, целое число больше 0",
        examples=[30],
    )
    ingredients: List[IngredientIn] = Field(
        ...,
        min_length=1,
        description="Список ингредиентов, минимум один",
        examples=[[{"name": "Мука", "amount": "200 г"}, {"name": "Молоко", "amount": "500 мл"}]],
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Текстовое описание: шаги приготовления",
        examples=["Смешать муку с молоком и яйцами, жарить на разогретой сковороде."],
    )


class RecipeListItem(BaseModel):
    """Строка таблицы на первом экране — краткая информация о рецепте."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ..., description="Идентификатор рецепта для перехода на детальный экран", examples=[1]
    )
    title: str = Field(..., description="Название блюда", examples=["Блины"])
    views: int = Field(
        ..., ge=0, description="Сколько раз открывали детальный рецепт", examples=[42]
    )
    cooking_time: int = Field(..., description="Время приготовления в минутах", examples=[30])


class RecipeDetail(BaseModel):
    """Детальная информация о рецепте — второй экран."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Идентификатор рецепта", examples=[1])
    title: str = Field(..., description="Название блюда", examples=["Блины"])
    cooking_time: int = Field(..., description="Время приготовления в минутах", examples=[30])
    ingredients: List[IngredientOut] = Field(
        ..., description="Список ингредиентов в порядке добавления"
    )
    description: str = Field(..., description="Текстовое описание рецепта")
    views: int = Field(
        ..., ge=0, description="Сколько раз открывали детальный рецепт, включая текущий просмотр"
    )


class ErrorResponse(BaseModel):
    """Ответ с ошибкой."""

    detail: str = Field(
        ..., description="Описание ошибки", examples=["Recipe with id 999 not found"]
    )
