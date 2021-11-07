from flask import Flask, request
import json
import ccxt
import re
import requests
import time
from datetime import datetime

config = json.load(open('config.json'))
gateio = {}
okex = {}
mexc = {}
gateio['usdtQuantity'] = 5000
mexc['usdtQuantity'] = 2000
okex['usdtQuantity'] = 500

def gateioInit(config):
    global gateio
    gateio["spot"] = ccxt.gateio(config["gate"])
    gateio["spot"].load_markets()

# gate sell
def gateioSell(coin, gateio):
    quantity = 0
    request = {}
    accounts = gateio["spot"].privateSpotGetAccounts(request)
    for account in accounts:
        if account['currency'] == coin:
            quantity = account["available"]
            break
    pair = coin + "_USDT"
    request = {
        'currency_pair': pair,
    }
    price = float(gateio["spot"].publicSpotGetOrderBook(request)['bids'][9][0])

    request = {
        'currency_pair': pair,
        'amount': gateio["spot"].amount_to_precision(pair, quantity),
        'price': gateio["spot"].price_to_precision(pair, price),
        'side': "sell",
    }
    try:
        gateio["spot"].privateSpotPostOrders(request)
    except Exception as e:
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e)
        pass
        return
    return request

# gate buy
def gateioTrade(coin, gateio):
    gateio["spot"].load_markets()
    usdtQuantity = gateio['usdtQuantity']
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
    okex["spot"].load_markets()
    usdtQuantity = okex['usdtQuantity']
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
    mexc["spot"].load_markets()
    usdtQuantity = mexc['usdtQuantity']
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
# Mexc Sell
def mexcSell(coin, mexc):
    account = mexc["spot"].spotPrivateGetAccountInfo({})
    quantity = account['data'][coin]['available']
    pair = coin + "_USDT"
    data = get_depth(pair, 10)
    price = float(data["data"]["bids"][9]["price"])
    request = {
        'symbol': pair,
        'price': mexc["spot"].price_to_precision(pair, price),
        'quantity': mexc["spot"].amount_to_precision(pair, quantity),
        'trade_type': 'ASK',
        'order_type': 'LIMIT_ORDER'
    }
    mexc["spot"].spotPrivatePostOrderPlace(request)
    return request

app = Flask(__name__)
@app.route('/', methods=['POST'])
def result():
    data = request.json
    print(data)
    coins = []
    if re.findall(r'币安.*上市', data["data"]):
        coins += re.findall(r'\（(.*?)\）', data["data"])
    if not coins and re.findall(r'幣安.*上市', data["data"]):
        coins += re.findall(r'\（(.*?)\）', data["data"])
    if not coins and re.findall(r'Binance.*Will List', data["data"]):
        coins += re.findall(r'\((.*?)\)', data["data"])
    if not coins and re.findall(r'거래.*디지털 자산 추가', data["data"]):
        tmp = re.findall(r'\((.*)\)', data["data"])
        if tmp:
            coins += re.split(', |,', tmp[0])
    if not coins and re.findall(r'市场数字资产新增', data["data"]):
        tmp = re.findall(r'（(.*)）', data["data"])
        if tmp:
            coins += re.split('、', tmp[0])
    
    text = ""
    for coin in coins:
        print(coin)
        try:
            r = gateioTrade(coin, gateio)
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "Gate.io" + " BUY OK\n" + str(r) + "\n"
            print(text)
        except Exception as err:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "Gate.io" + " MISS!" + "\n"
            print(text, err)
            pass

        try:
            r = mexcTrade(coin, mexc)
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "Mexc" + " BUY OK\n" + str(r) + "\n"
            print(text)  
        except Exception as err:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "Mexc" + " MISS!" + "\n"
            print(text, err)
            pass

        # OKEX
        try:
            r = okexTrade(coin, okex)
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "okex" + " BUY OK\n" + str(r) + "\n"
            print(text)
        except Exception as err:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "okex" + " MISS!" + "\n"
            print(text, err)
            pass

        # SELL
        time.sleep(3)
        try:
            r = gateioSell(coin, gateio)
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "Gate.io" + " SELL OK\n" + str(r) + "\n"
            print(text)
        except Exception as err:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "Gate.io" + " SELL FAIL!" + "\n"
            print(text, err)
            pass

        try:
            r = mexcSell(coin, mexc)
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "Mexc" + " SELL OK\n" + str(r) + "\n"
            print(text)
        except Exception as err:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            text = "Mexc" + " SELL FAIL!" + "\n"
            print(text, err)
            pass

    return "<p>OK</p>"



if __name__ == '__main__':
    gateioInit(config)
    okexInit(config)
    mexcInit(config)
    app.run()
