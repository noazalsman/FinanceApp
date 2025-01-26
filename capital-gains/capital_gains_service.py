from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import requests

app = Flask(__name__)

load_dotenv()
port = os.getenv("FLASK_PORT", 8080)

@app.route('/capital-gains', methods=['GET'])
def get_capital_gains():
    try:
        # Get query parameters
        num_shares_gt = request.args.get('numsharegt', type=int)
        num_shares_lt = request.args.get('numsharelt', type=int)

        response1 = requests.get('http://stocks-svr:8000/stocks')
        stocks1 = response1.json()
        
        if num_shares_gt is not None:
            stocks1 = list(filter(lambda s1: s1["shares"] > num_shares_gt, stocks1))
                
        if num_shares_lt is not None:
            stocks1 = list(filter(lambda s1: s1["shares"] < num_shares_lt, stocks1))
        
        sum1 = 0.0
        for s1 in stocks1:
            response = requests.get(f"http://stocks-svr:8000/stock-value/{s1['_id']}")
            sum1 += response.json()["stock value"]

        total_purchase_price = sum(s1["purchase price"] * s1["shares"] for s1 in stocks1)
        capital_gains = sum1 - total_purchase_price
        
        return jsonify({"capital gains": round(capital_gains, 2)}), 200
    
    except Exception as e:
        print("Exception: ", str(e))
        return jsonify({"server error": str(e)}), 500
        
if __name__ == '__main__':
    print("Running Capital Gains Service")
    app.run(host='0.0.0.0', port=port, debug=True)


