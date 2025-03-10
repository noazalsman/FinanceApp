import pytest
import requests
import os
import json

BASE_URL = "http://localhost:5001"

@pytest.fixture
def stock_details():
    stock_data = {}
    stock_dir = "./stock-objects"

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
    assert len(data) == 2  # Ensure there are 3 stocks
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


# Tester code

# import requests
# import pytest

# BASE_URL = "http://localhost:5001" 

# # Stock data
# stock1 = { "name": "NVIDIA Corporation", "symbol": "NVDA", "purchase price": 134.66, "purchase date": "18-06-2024", "shares": 7 }
# stock2 = { "name": "Apple Inc.", "symbol": "AAPL", "purchase price": 183.63, "purchase date": "22-02-2024", "shares": 19 }
# stock3 = { "name": "Alphabet Inc.", "symbol": "GOOG", "purchase price": 140.12, "purchase date": "24-10-2024", "shares": 14 }

# def test_post_stocks():
#     response1 = requests.post(f"{BASE_URL}/stocks", json=stock1)
#     response2 = requests.post(f"{BASE_URL}/stocks", json=stock2)
#     response3 = requests.post(f"{BASE_URL}/stocks", json=stock3)
    
#     assert response1.status_code == 201
#     assert response2.status_code == 201
#     assert response3.status_code == 201

#     # Ensure unique IDs
#     data1 = response1.json()
#     data2 = response2.json()
#     data3 = response3.json()
#     assert data1['id'] != data2['id']
#     assert data1['id'] != data3['id']
#     assert data2['id'] != data3['id']

# def test_get_stocks():
#     response = requests.get(f"{BASE_URL}/stocks")
#     assert response.status_code == 200
#     stocks = response.json()
#     assert len(stocks) == 3 
    
# def test_get_portfolio_value():
#     response = requests.get(f"{BASE_URL}/portfolio-value")
#     assert response.status_code == 200
#     portfolio_value = response.json()
#     assert portfolio_value['portfolio value'] > 0  # Portfolio value should be greater than 0

# def test_post_stocks_invalid_data():
#     stock_invalid = { "name": "Amazon", "purchase price": 100.50, "purchase date": "15-03-2025", "shares": 50 }
#     response = requests.post(f"{BASE_URL}/stocks", json=stock_invalid)
#     assert response.status_code == 400
