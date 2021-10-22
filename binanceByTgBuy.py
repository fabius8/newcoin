from flask import Flask, request
import json
import ccxt
import re
import requests

config = json.load(open('config.json'))
gateio = {}
okex = {}
mexc = {}

def gateioInit(config):
    global gateio
    gateio["spot"] = ccxt.gateio(config["gate"])
    gateio["spot"].load_markets()

def gateioTrade(coin, gateio):
    usdtQuantity = 1000
    pair = coin + "_USDT"
    request = {
        'currency_pair': pair,
    }
    price = float(gateio["spot"].publicSpotGetOrderBook(request)['asks'][9][0])
    request = {
        'currency_pair': pair,
        'amount': gateio["spot"].amount_to_precision(pair, usdtQuantity/price),
        'price': gateio["spot"].price_to_precision(pair, price),
        'side': "buy",
    }
    gateio["spot"].privateSpotPostOrders(request)
    return request

def okexInit(config):
    global okex
    okex["spot"] = ccxt.okex5(config["okex"])
    okex["spot"].load_markets()

def okexTrade(coin, okex):
    usdtQuantity = 500
    pair = coin + "-USDT"
    request = {
        "instId": pair,
        "tdMode": "cash",
        "side": "buy",
        "ordType": "market",
        "sz": usdtQuantity
    }
    okex["spot"].private_post_trade_order(request)
    return request

ROOT_URL = 'https://www.mxc.com'
def get_depth(symbol, depth):
    """market depth"""
    method = 'GET'
    path = '/open/api/v2/market/depth'
    url = '{}{}'.format(ROOT_URL, path)
    params = {
        'symbol': symbol,
        'depth': depth,
    }
    response = requests.request(method, url, params=params)
    return response.json()

def mexcInit(config):
    global mexc
    mexc["spot"] = ccxt.mexc(config["mexc"])
    mexc["spot"].load_markets()

def mexcTrade(coin, mexc):
    usdtQuantity = 500
    pair = coin + "_USDT"
    data = get_depth(pair, 10)
    price = float(data["data"]["asks"][9]["price"])
    request = {
        'symbol': pair,
        'price': mexc["spot"].price_to_precision(pair, price),
        'quantity': mexc["spot"].amount_to_precision(pair, usdtQuantity/price),
        'trade_type': 'BID',
        'order_type': 'LIMIT_ORDER'
    }
    mexc["spot"].spotPrivatePostOrderPlace(request)
    return request

app = Flask(__name__)
@app.route('/', methods=['POST'])
def result():
    data = request.json
    coins = []
    coins += re.findall(r'幣安.*上市.*（(.*?)）', data["data"])
    coins += re.findall(r'Binance.*Will List.*\((.*?)\)', data["data"])
    text = ""
    if coins:
        print(data)
        try:
            r = gateioTrade(coins[0], gateio)
            text = "Gate.io" + " BUY OK\n" + str(r) + "\n"
            print(text)  
        except Exception as err:
            text = "Gate.io" + " MISS!" + "\n"
            print(text, err)
            pass

        try:
            r = mexcTrade(coins[0], mexc)
            text = "Mexc" + " BUY OK\n" + str(r) + "\n"
            print(text)  
        except Exception as err:
            text = "Mexc" + " MISS!" + "\n"
            print(text, err)
            pass

        # OKEX
        try:
            r = okexTrade(coins[0], okex)
            text = "okex" + " BUY OK\n" + str(r) + "\n"
            print(text)  
        except Exception as err:
            text = "okex" + " MISS!" + "\n"
            print(text, err)
            pass

    return "<p>OK</p>"



if __name__ == '__main__':
    gateioInit(config)
    okexInit(config)
    mexcInit(config)
    app.run()
