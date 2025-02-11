import pytest
import requests
import os

BASE_URL = "http://localhost:5001"

@pytest.fixture
def stock_details():
    stock_data = {}
    stock_dir = "tests/stock-objects"

    for file in os.listdir(stock_dir):
        if file.endswith(".json"):
            with open(os.path.join(stock_dir, file), "r") as f:
                stock_data[file.replace(".json", "")] = json.load(f)

    return stock_data

@pytest.fixture(scope="session")
def created_stock_ids():
    return {}

@pytest.fixture(scope="session")
def stock_values():
    return {}


@pytest.mark.dependency()
def test_create_stocks(stock_details, created_stock_ids):
    for stock_key in ["stock1", "stock2", "stock3"]:
        response = requests.post(f"{BASE_URL}/stocks", json=stock_details[stock_key])
        assert response.status_code == 201
        created_stock_ids[stock_key] = response.json().get("id")
    
    # Ensure all IDs are unique
    ids = list(created_stock_ids.values())
    assert len(ids) == len(set(ids))


@pytest.mark.dependency(depends=["test_create_stocks"])
def test_get_stock_by_id(created_stock_ids):
    stock1_id = created_stock_ids.get("stock1")

    # Retrieve stock1 by ID
    response = requests.get(f"{BASE_URL}/stocks/{stock1_id}")
    data = response.json()

    assert data["symbol"] == "NVDA"
    assert response.status_code == 200


@pytest.mark.dependency(depends=["test_create_stocks"])
def test_get_all_stocks(stock_details):
    response = requests.get(f"{BASE_URL}/stocks")
    data = response.json()
    assert len(data) == 3  # Ensure there are 3 stocks
    assert response.status_code == 200


@pytest.mark.dependency(depends=["test_create_stocks"])
def test_get_stock_values(stock_details, created_stock_ids, stock_values):
    for stock_key, stock_id in created_stock_ids.items():
        response = requests.get(f"{BASE_URL}/stock-value/{stock_id}")
        data = response.json()
        stock_values[stock_key] = data["stock value"]

        assert data["symbol"] == stock_details[stock_key]["symbol"]
        assert response.status_code == 200


@pytest.mark.dependency(depends=["test_get_stock_values"])
def test_get_portfolio_value(stock_values):
    sv1 = stock_values.get("stock1", 0)
    sv2 = stock_values.get("stock2", 0)
    sv3 = stock_values.get("stock3", 0)
    total_stock_value = sv1 + sv2 + sv3

    response = requests.get(f"{BASE_URL}/portfolio-value")
    assert response.status_code == 200

    portfolio_value = response.json().get("portfolio value")
    assert portfolio_value * 0.97 <= total_stock_value <= portfolio_value * 1.03


def test_invalid_stock_creation_missing_symbol(stock_details):
    response = requests.post(f"{BASE_URL}/stocks", json=stock_details["stock7"])
    assert response.status_code == 400


@pytest.mark.dependency(depends=["test_create_stocks"])
def test_delete_stock(created_stock_ids):
    stock2_id = created_stock_ids.get("stock2")
    response = requests.delete(f"{BASE_URL}/stocks/{stock2_id}")
    assert response.status_code == 200


@pytest.mark.dependency(depends=["test_delete_stock"])
def test_get_deleted_stock_by_id(created_stock_ids):
    stock2_id = created_stock_ids.get("stock2")
    response = requests.get(f"{BASE_URL}/stocks/{stock2_id}")
    assert response.status_code == 404


def test_invalid_stock_creation_incorrect_date(stock_details):
    response = requests.post(f"{BASE_URL}/stocks", json=stock_details["stock8"])
    assert response.status_code == 400

