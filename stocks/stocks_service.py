from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
import pymongo
from bson import ObjectId

app = Flask(__name__)

load_dotenv()
flask_port = os.getenv("FLASK_PORT", 8000)
mongo_port = os.getenv("MONGO_PORT", 27017)
collection_name = os.getenv("COLLECTION_NAME", "stocks")
API_KEY = os.getenv("NINJA_API_KEY")

client = pymongo.MongoClient(f"mongodb://mongo:{mongo_port}/")
db = client["stocksDB"]
stocks_collection = db[collection_name]

def get_curr_stock_values(id):
    stock = stocks_collection.find_one({"_id": ObjectId(id)})
    if stock is None:
        return jsonify({"error": "Not found"}), 404
    symbol = stock["symbol"]
    api_url = 'https://api.api-ninjas.com/v1/stockprice?ticker={}'.format(symbol)
    response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
    if response.status_code == requests.codes.ok:
        stock_current_price = response.json()["price"]
    else:
        return jsonify({"server error": "API resonse code " + str(response.status_code)}), 500
    stock_value = stock_current_price * stock["shares"]
    return symbol, round(stock_current_price, 2), round(stock_value, 2)

def is_date_in_format(date_str):
    try:
        # Attempt to parse the date string in the specified format
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        # If parsing fails, the format is incorrect
        return False

@app.route('/stocks', methods=['POST'])
def add_stock():
    print("POST stocks")
    try:
        content_type = request.headers.get("Content-Type")
        if content_type != 'application/json':
            return jsonify({"error": "Expected application/json media type"}), 415
        data = request.get_json()
        required_fields = ["symbol", "purchase price", "shares"]
        if not all(field in data for field in required_fields) or not is_date_in_format(data["purchase date"]):
            return jsonify({"error": "Malformed data"}), 400
        stocks_items = list(stocks_collection.find())
        if any(data["symbol"] == stock["symbol"] for stock in stocks_items):
            return jsonify({"error": "Malformed data"}), 400
        if "name" not in data:
            data["name"] = "NA"
        if "purchase date" not in data:
            data["purchase date"] = "NA"
        new_stock = {
            "name": data["name"],
            "symbol": data["symbol"],
            "purchase price": round(data["purchase price"], 2),
            "purchase date": data["purchase date"],
            "shares": data["shares"]
        }
        response = stocks_collection.insert_one(new_stock)
        return jsonify({"id": str(response.inserted_id)}), 201
    except Exception as e:
        print("Exception: ", str(e))
        return jsonify({"server error": str(e)}), 500

@app.route('/stocks', methods=['GET'])
def get_stocks():
    try:
        query_params = request.args
        stocks_items = list(stocks_collection.find())
        for stock in stocks_items:
            stock['_id'] = str(stock['_id'])
        if query_params:
            filtered_stocks = [
                stock for stock in stocks_items
                if all(str(stock.get(key, "")) == value for key, value in query_params.items())
            ]
            return filtered_stocks, 200
        return list(stocks_items), 200
    except Exception as e:
        print("Exception: ", str(e))
        return jsonify({"server error": str(e)}), 500

@app.route('/stocks/<id>', methods=['GET'])
def get_stock(id):
    try:
        stock = stocks_collection.find_one({"_id": ObjectId(id)})
        if stock is None:
            return jsonify({"error": "Not found"}), 404
        stock['_id'] = str(stock['_id'])
        return jsonify(stock), 200
    except Exception as e:
        print("Exception: ", str(e))
        return jsonify({"server error": str(e)}), 500
    
@app.route('/stocks/<id>', methods=['DELETE'])
def del_stock(id):
    try:
        stock = stocks_collection.delete_one({"_id": ObjectId(id)})
        if stock is None:
            return jsonify({"error": "Not found"}), 404
        return '', 200
    except Exception as e:
        print("Exception: ", str(e))
        return jsonify({"server error": str(e)}), 500

@app.route('/stocks/<id>', methods=['PUT'])
def update(id):
    try:
        content_type = request.headers.get("Content-Type")
        if content_type != 'application/json':
            return jsonify({"error": "Expected application/json media type"}), 415
        data = request.get_json()
        required_fields = ["id", "name", "symbol", "purchase price", "purchase date", "shares"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Malformed data"}), 400
        stock = stocks_collection.find_one({"_id": ObjectId(id)})
        if stock is None:
            return jsonify({"error": "Not found"}), 404
        updated_stock = {
            "name": data["name"],
            "symbol": data["symbol"],
            "purchase price": round(data["purchase price"] ,2),
            "purchase date": data["purchase date"],
            "shares": data["shares"]
        }
        stocks_collection.update_one({"_id": ObjectId(id)}, {"$set": updated_stock})
        return jsonify({"id": id}), 200
    except Exception as e:
        print("Exception: ", str(e))
        return jsonify({"server error": str(e)}), 500

@app.route('/stock-value/<id>', methods=['GET'])
def get_stock_value(id):
    try:
        symbol, stock_current_price, stock_value = get_curr_stock_values(id)
        return jsonify({"symbol": symbol, "ticker": stock_current_price, "stock value": stock_value}), 200
    except Exception as e:
        print("Exception: ", str(e))
        return jsonify({"server error": str(e)}), 500

@app.route('/portfolio-value', methods=['GET'])
def get_portfolio_value():
    try:
        total_portfolio_value = 0.0
        stocks_items = list(stocks_collection.find())
        for stock in stocks_items:
           _, _, stock_value = get_curr_stock_values(str(stock["_id"]))
           total_portfolio_value += stock_value
        current_date = datetime.now().strftime('%d-%m-%Y')
        return jsonify({"date": current_date, "portfolio value": total_portfolio_value}), 200
    except Exception as e:
        print("Exception: ", str(e))
        return jsonify({"server error": str(e)}), 500
        
@app.route('/kill', methods=['GET'])
def kill_container():
    os._exit(1)

if __name__ == '__main__':
    print(f"Running {collection_name} service")
    app.run(host='0.0.0.0', port=flask_port, debug=True)


