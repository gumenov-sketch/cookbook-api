from typing import Any

from fastapi.testclient import TestClient


def create_recipe(client: TestClient, **fields: Any) -> dict[str, Any]:
    payload = {
        "title": "Рецепт",
        "cooking_time": 10,
        "ingredients": [{"name": "Вода", "amount": "1 л"}],
        "description": "Описание",
    }
    payload.update(fields)
    response = client.post("/recipes", json=payload)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def test_recipes_list_empty(client: TestClient) -> None:
    response = client.get("/recipes")
    assert response.status_code == 200
    assert response.json() == []


def test_create_recipe(client: TestClient, recipe_payload: dict[str, Any]) -> None:
    response = client.post("/recipes", json=recipe_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["title"] == "Блины"
    assert data["cooking_time"] == 40
    assert data["views"] == 0
    assert data["ingredients"] == recipe_payload["ingredients"]
    assert data["description"] == "Смешать и пожарить."


def test_ingredient_amount_is_optional(client: TestClient, recipe_payload: dict[str, Any]) -> None:
    recipe_payload["ingredients"] = [{"name": "Соль"}]
    response = client.post("/recipes", json=recipe_payload)
    assert response.status_code == 201
    assert response.json()["ingredients"] == [{"name": "Соль", "amount": ""}]


def test_list_item_fields(client: TestClient, recipe_payload: dict[str, Any]) -> None:
    created = client.post("/recipes", json=recipe_payload).json()
    items = client.get("/recipes").json()
    assert items == [{"id": created["id"], "title": "Блины", "views": 0, "cooking_time": 40}]


def test_detail_increments_views(client: TestClient, recipe_payload: dict[str, Any]) -> None:
    recipe_id = client.post("/recipes", json=recipe_payload).json()["id"]
    assert client.get(f"/recipes/{recipe_id}").json()["views"] == 1
    assert client.get(f"/recipes/{recipe_id}").json()["views"] == 2
    assert client.get("/recipes").json()[0]["views"] == 2


def test_list_does_not_increment_views(client: TestClient, recipe_payload: dict[str, Any]) -> None:
    client.post("/recipes", json=recipe_payload)
    client.get("/recipes")
    client.get("/recipes")
    assert client.get("/recipes").json()[0]["views"] == 0


def test_list_sorted_by_views_then_cooking_time(client: TestClient) -> None:
    slow = create_recipe(client, title="Долгий", cooking_time=120)
    create_recipe(client, title="Быстрый", cooking_time=5)
    popular = create_recipe(client, title="Популярный", cooking_time=60)
    medium = create_recipe(client, title="Средний", cooking_time=30)

    for _ in range(3):
        client.get(f"/recipes/{popular['id']}")
    client.get(f"/recipes/{slow['id']}")
    client.get(f"/recipes/{medium['id']}")

    titles = [item["title"] for item in client.get("/recipes").json()]
    # popular: 3 просмотра; medium и slow: по 1 — быстрее готовится medium; fast: 0.
    assert titles == ["Популярный", "Средний", "Долгий", "Быстрый"]


def test_get_missing_recipe(client: TestClient) -> None:
    response = client.get("/recipes/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Recipe with id 999 not found"}


def test_get_recipe_invalid_id(client: TestClient) -> None:
    assert client.get("/recipes/0").status_code == 422
    assert client.get("/recipes/abc").status_code == 422


def test_create_recipe_validation(client: TestClient, recipe_payload: dict[str, Any]) -> None:
    invalid_payloads = [
        {**recipe_payload, "title": ""},
        {**recipe_payload, "cooking_time": 0},
        {**recipe_payload, "cooking_time": "долго"},
        {**recipe_payload, "ingredients": []},
        {**recipe_payload, "ingredients": [{"name": ""}]},
        {key: value for key, value in recipe_payload.items() if key != "description"},
    ]
    for payload in invalid_payloads:
        assert client.post("/recipes", json=payload).status_code == 422, payload
    assert client.get("/recipes").json() == []


def test_openapi_documents_models(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert {"/recipes", "/recipes/{recipe_id}"} <= set(schema["paths"])
    components = schema["components"]["schemas"]
    for model in (
        "RecipeCreate",
        "RecipeListItem",
        "RecipeDetail",
        "IngredientIn",
        "IngredientOut",
        "ErrorResponse",
    ):
        assert model in components
    assert components["RecipeListItem"]["properties"]["views"]["description"]
    assert "404" in schema["paths"]["/recipes/{recipe_id}"]["get"]["responses"]
