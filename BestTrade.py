from bs4 import BeautifulSoup
import re
import time
import requests
import json
from datetime import datetime
import ccxt
import sys

if len(sys.argv) == 2:
    site = sys.argv[1]
else:
    site = "binancezh.top"

config = json.load(open('config.json'))
errCount = 0
binance_announcement_site = "https://www." + site + "/en/support/announcement"
previousAnn = None
gateio = {}
okex = {}
mexc = {}
interval = 1

def gateioInit(config):
    global gateio
    gateio["spot"] = ccxt.gateio(config["gate"])
    gateio["spot"].load_markets()

def gateioTrade(coin, gateio):
    usdtQuantity = 500
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

# MEXC
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


def sendmsg(text):
    params = {
        "corpid": config['corpid'],
        "corpsecret": config['corpsecret']
    }
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    r = requests.get(url, params = params)
    access_token = r.json()["access_token"]
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
    params = {
        "access_token": access_token
    }
    data = {
        "touser": "@all",
        "msgtype" : "text",
        "agentid" : 1000004,
        "text" : {
            "content" : text
        }
    }
    r = requests.post(url, params = params, json = data)

def getBinanceAnnCoin():
    global previousAnn
    global errCount
    try:
        r = requests.get(binance_announcement_site, timeout=5)
    except requests.exceptions.RequestException as e:
        print(e, errCount)
        errCount += 1
        return {}
    soup = BeautifulSoup(r.text, "html.parser")
    data = soup.find(id="__APP_DATA")
    AnnCoin = json.loads(data.string)["routeProps"]["42b1"]["catalogs"][0]["articles"][0]
    if AnnCoin == previousAnn:
        return {}
    elif previousAnn is None:
        previousAnn = AnnCoin
        return {}
    else:
        #there is new coin list
        if "Will List" in AnnCoin['title']:
            coins = re.findall(r'\((.*?)\)', AnnCoin['title'])
            previousAnn = AnnCoin
            return coins
        previousAnn = AnnCoin
        return {}


if __name__ == "__main__":
    count = 0
    gateioInit(config)
    okexInit(config)
    mexcInit(config)
    coins = getBinanceAnnCoin()
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "Start...")

    while True:
        count += 1
        coins = getBinanceAnnCoin()
        text = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + " count:" + str(count) + " err:" + str(errCount) + "\n"
        for i in coins:
            text += "Binance Announcement List (" + i + ")\n"

            # Gateio
            try:
                r = gateioTrade(i, gateio)
                text += "Gate.io" + " BUY OK\n" + str(r) + "\n"
                print(text)  
            except Exception as err:
                text += "Gate.io" + " MISS!" + "\n"
                print(err)
                pass
            # MEXC
            try:
                r = mexcTrade(i, mexc)
                text += "Mexc" + " BUY OK\n" + str(r) + "\n"
                print(text)  
            except Exception as err:
                text += "Mexc" + " MISS!" + "\n"
                print(err)
                pass

            # OKEX
            try:
                r = okexTrade(i, okex)
                text += "okex" + " BUY OK\n" + str(r) + "\n"
                print(text)  
            except Exception as err:
                text += "okex" + " MISS!" + "\n"
                print(err)
                pass

            sendmsg(text)
        time.sleep(interval)
