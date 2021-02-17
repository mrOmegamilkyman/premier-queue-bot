import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
TD_CONSUMER_KEY = os.getenv('TD_CONSUMER_KEY')
TD_REFRESH_TOKEN = os.getenv('TD_REFRESH_TOKEN')
URL_ENCODED_REDIRECT_URI = "https%3A%2F%2Flocalhost%3A8080%2Fcallback"

CAPITAL_ALLOCATION_RATE = 0.3
ROLLING_STOP_LOSS = 0.1


def get_stock_data(ticker: str):
    endpoint = f'https://api.tdameritrade.com/v1/marketdata/{ticker}/quotes?apikey={TD_CONSUMER_KEY}'
    page = requests.get(url=endpoint)
    content = json.loads(page.content)
    stock_data = content[ticker]
    return stock_data


# WIP I think doing this by hand i just a better solution for now
def get_access_token():
    endpoint = "https://api.tdameritrade.com/v1/oauth2/token"
    params = {
        "grant_type" : "refresh_token",
        "refresh_token" : TD_REFRESH_TOKEN,
        "access_type":"",
        "code":"",
        "client_id" : f"{TD_CONSUMER_KEY}",
        "redirect_uri":""
    }
    page = requests.post(url=endpoint, params=params)
    content = json.loads(page.content)
    print(content)
    access_token = content["access_token"]
    return access_token

print(get_access_token())

def get_accounts(access_token):
    endpoint = "https://api.tdameritrade.com/v1/accounts"
    headers = {"authorization": f"Bearer {access_token}"}
    page = requests.get(url=endpoint, headers=headers)
    content = json.loads(page.content)
    return content


def set_position(ticker):
    token = get_access_token()
    
    ask_price = get_stock_data(ticker)["askPrice"]
    accounts = get_accounts(token)
    available_cash = accounts["securitiesAccount"]["currentBalances"]["cashAvailableForTrading"]
    trade_allocation = available_cash * CAPITAL_ALLOCATION_RATE
    
    total_shares = floor(trade_allocation/ask_price)

    print(f"TICKER: {Ticker}")
    print(f"ASK PRICE: ${ask_price}")
    print(f"ALLOCATION RATE: {CAPITAL_ALLOCATION_RATE*100}%")
    print(f"TRADE ALLOCATION: {trade_allocation}")
    print(f"BUYING: {total_shares} Shares")
    print(f"TOTAL COST: ${total_shares*ask_price}")
