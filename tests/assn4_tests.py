import pytest
import requests

BASE_URL = "http://localhost:5001"  # Replace with your actual base URL

@pytest.fixture
def stock_details():
    return {
        "stock1": {
            "name": "NVIDIA Corporation",
            "symbol": "NVDA",
            "purchase price": 134.66,
            "purchase date": "18-06-2024",
            "shares": 7
        },
        "stock2": {
            "name": "Apple Inc.",
            "symbol": "AAPL",
            "purchase price": 183.63,
            "purchase date": "22-02-2024",
            "shares": 19
        },
        "stock3": {
            "name": "Alphabet Inc.",
            "symbol": "GOOG",
            "purchase price": 140.12,
            "purchase date": "24-10-2024",
            "shares": 14
        },
        "stock4": {
            "name": "Tesla, Inc.",
            "symbol": "TSLA",
            "purchase price": 194.58,
            "purchase date": "28-11-2022",
            "shares": 32
        },
        "stock5": {
            "name": "Microsoft Corporation",
            "symbol": "MSFT",
            "purchase price": 420.55,
            "purchase date": "09-02-2024",
            "shares": 35
        },
        "stock6": {
            "name": "Intel Corporation",
            "symbol": "INTC",
            "purchase price": 19.15,
            "purchase date": "13-01-2025",
            "shares": 10
        },
        "stock7": {
            "name": "Amazon.com, Inc.",
            "purchase price": 134.66,
            "purchase date": "18-06-2024",
            "shares": 7
        },  # Missing "symbol"
        "stock8": {
            "name": "Amazon.com, Inc.",
            "symbol": "AMZN",
            "purchase price": 134.66,
            "purchase date": "Tuesday, June 18, 2024",
            "shares": 7
        }  # Incorrect date format
    }

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


def test_invalid_stock_creation_incorrect_date(stocks_details):
    response = requests.post(f"{BASE_URL}/stocks", json=stocks_details["stock8"])
    assert response.status_code == 400

