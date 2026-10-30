# Кулинарная книга — API

[![CI](https://github.com/gumenov-sketch/cookbook-api/actions/workflows/ci.yml/badge.svg)](https://github.com/gumenov-sketch/cookbook-api/actions/workflows/ci.yml)

Асинхронный сервис на **FastAPI** и **асинхронной SQLAlchemy** (SQLite через `aiosqlite`).

## Запуск

```
pip install -r requirements.txt
uvicorn app.main:app --reload
```

При первом старте создаётся база `recipes.db` с тремя примерами рецептов.
Другую базу можно указать переменной окружения `DATABASE_URL`
(например, `postgresql+asyncpg://user:pass@localhost/recipes`).

Документация для фронтенда генерируется автоматически:

* Swagger UI — http://127.0.0.1:8000/docs (можно отправлять запросы прямо из браузера)
* ReDoc — http://127.0.0.1:8000/redoc
* OpenAPI-схема — http://127.0.0.1:8000/openapi.json

## Эндпоинты

| Метод | URL | Экран | Ответ |
|---|---|---|---|
| GET | `/recipes` | 1 — таблица рецептов | `200`, список `RecipeListItem` |
| GET | `/recipes/{recipe_id}` | 2 — детальный рецепт | `200` `RecipeDetail`, `404` если нет, `422` если id не целое > 0 |
| POST | `/recipes` | создание рецепта | `201` `RecipeDetail`, `422` при ошибке валидации |

### Сортировка списка

По убыванию `views` (сколько раз открывали детальный рецепт), при равенстве — по возрастанию
`cooking_time`. Запрос списка просмотры не увеличивает. Каждый `GET /recipes/{recipe_id}` увеличивает
`views` на 1 атомарным `UPDATE` в базе, поэтому одновременные просмотры не теряются.

### Модели

`RecipeListItem` — строка таблицы:

```json
{"id": 1, "title": "Блины", "views": 42, "cooking_time": 40}
```

`RecipeDetail` — детальный рецепт:

```json
{
  "id": 1,
  "title": "Блины",
  "cooking_time": 40,
  "ingredients": [{"name": "Мука", "amount": "200 г"}, {"name": "Молоко", "amount": "500 мл"}],
  "description": "Смешать яйца с сахаром ...",
  "views": 43
}
```

`RecipeCreate` — тело `POST /recipes`:

| Поле | Тип | Ограничения |
|---|---|---|
| `title` | string | 1–200 символов |
| `cooking_time` | integer | минуты, больше 0 |
| `ingredients` | array of `{name, amount}` | минимум один; `name` 1–100 символов, `amount` до 50 символов, необязателен |
| `description` | string | не пустое |

Ошибка `404`: `{"detail": "Recipe with id 999 not found"}`.

## Структура

```
app/
  database.py  — асинхронный engine, сессии, зависимость get_session
  models.py    — ORM-модели Recipe и Ingredient (один ко многим, каскадное удаление)
  schemas.py   — Pydantic-схемы запросов и ответов с описаниями для документации
  seed.py      — примеры рецептов для пустой базы
  main.py      — приложение FastAPI и эндпоинты
tests/         — тесты pytest (каждый тест на своей временной базе)
```

## Тесты и линтеры

```
pip install -r requirements-dev.txt
pytest -v
black --check .
isort --check-only .
flake8 .
mypy app tests
```

Настройки: `pyproject.toml` (black, isort, mypy в строгом режиме с плагином pydantic, pytest) и `.flake8`.

## CI

GitHub Actions (`.github/workflows/ci.yml`) запускается на каждый пуш в любую ветку и на каждый pull request.
Два параллельных job:

* **lint** — `black --check`, `isort --check-only`, `flake8`, `mypy`;
* **test** — `pytest`.

Если любая проверка падает, CI красный — такой код не мержим (quality gate).
