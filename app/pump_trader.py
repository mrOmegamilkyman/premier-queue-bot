import os
import json
import requests
import math
from dotenv import load_dotenv

load_dotenv()
TD_ACCOUNT_NUMBER = os.getenv('TD_ACCOUNT_NUMBER')
TD_CONSUMER_KEY = os.getenv('TD_CONSUMER_KEY')
TD_REFRESH_TOKEN = os.getenv('TD_REFRESH_TOKEN')
URL_ENCODED_REDIRECT_URI = "https%3A%2F%2Flocalhost%3A8080%2Fcallback"

CAPITAL_ALLOCATION_RATE = 0.25
ROLLING_STOP_LOSS = 0.10


#This only really needs to be called like every 30 minutes but it doesnt blow up if i get a new one for every time sooooo.......
def get_access_token():
    endpoint = 'https://api.tdameritrade.com/v1/oauth2/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': TD_REFRESH_TOKEN,
        'access_type': '',
        'code': '',
        'client_id': TD_CONSUMER_KEY,
        'redirect_uri': ''
    }
    response = requests.post(endpoint, headers=headers, data=data)
    content = json.loads(response.content)
    access_token = content["access_token"]
    return access_token


def get_stock_data(ticker, access_token=None):
    if access_token == None:
        endpoint = f'https://api.tdameritrade.com/v1/marketdata/{ticker}/quotes?apikey={TD_CONSUMER_KEY}'
        response = requests.get(url=endpoint)
        content = json.loads(response.content)
        stock_data = content[ticker]
    else:
        endpoint = f'https://api.tdameritrade.com/v1/marketdata/{ticker}/quotes'
        headers = {
            'Authorization':f'Bearer {access_token}'
            }
        response = requests.get(url=endpoint, headers=headers)
        content = json.loads(response.content)
        stock_data = content[ticker]
    return stock_data


def get_accounts(access_token):
    endpoint = "https://api.tdameritrade.com/v1/accounts"
    headers = {"authorization": f"Bearer {access_token}"}
    response = requests.get(url=endpoint, headers=headers)
    content = json.loads(response.content)
    return content


def send_order(ticker, amount, access_token):
    endpoint = f'https://api.tdameritrade.com/v1/accounts/{TD_ACCOUNT_NUMBER}/orders'
    headers = {"Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
    }
    data = {
        "complexOrderStrategyType": "NONE",
        "orderType": "TRAILING_STOP",
        "session": "NORMAL",
        "stopPriceLinkBasis": "BID",
        "stopPriceLinkType": "PERCENT",
        "stopPriceOffset": int(100*ROLLING_STOP_LOSS),
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
            "instruction": "BUY",
            "quantity": amount,
            "instrument": {
                "symbol": ticker,
                "assetType": "EQUITY"
            }
            }
        ]
    }
    data = json.dumps(data)
    response = requests.post(url=endpoint, headers=headers, data=data)
    content = json.loads(response.content)
    print(content)
    return content


def set_position(ticker):
    token = get_access_token()
    ask_price = get_stock_data(ticker, token)["askPrice"]
    accounts = get_accounts(token)
    available_cash = accounts[0]["securitiesAccount"]["currentBalances"]["cashAvailableForTrading"]
    trade_allocation = available_cash * CAPITAL_ALLOCATION_RATE
    
    total_shares = math.floor(trade_allocation/ask_price)

    print(f"TICKER: {ticker}")
    print(f"ASK PRICE: ${ask_price}")
    print(f"ALLOCATION RATE: {CAPITAL_ALLOCATION_RATE*100}%")
    print(f"TRADE ALLOCATION: ${trade_allocation}")
    print(f"BUYING: {total_shares} Shares")
    print(f"TOTAL COST: ${total_shares*ask_price}")

set_position("NTIP")
send_order("NTIP", 1, get_access_token())
