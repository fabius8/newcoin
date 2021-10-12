
from bs4 import BeautifulSoup
import re
import time
import requests
import json
from datetime import datetime
import ccxt

config = json.load(open('config.json'))
errCount = 0
binance_announcement_site = "https://www.binance.com/en/support/announcement"
previousAnn = None
gateio = {"coinlist":[]}

def gateioInit(config):
    global gate
    gateio["spot"] = ccxt.gateio(config["gate"])
    gateio["spot"].load_markets()


def gateioTrade(coin, gateio):
    usdtQuantity = 500
    pair = coin + "_USDT"
    request = {
        'currency_pair': pair,
    }
    price = float(gateio["spot"].publicSpotGetOrderBook(request)['asks'][0][0])
    request = {
        'currency_pair': pair,
        'amount': gateio["spot"].amount_to_precision(pair, usdtQuantity/price),
        'price': gateio["spot"].price_to_precision(pair, price),
        'side': "buy",
    }
    gateio["spot"].privateSpotPostOrders(request)
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
            return coins
        previousAnn = AnnCoin
        return {}


if __name__ == "__main__":
    count = 0
    gateioInit(config)
    coins = getBinanceAnnCoin()

    while True:
        count += 1
        coins = getBinanceAnnCoin()
        text = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + " count:" + str(count) + " err:" + str(errCount)
        for i in coins:
            try:
                r = gateioTrade(i, gateio)
                text += " gateio" + " buy OK" + str(r)
            except Exception as err:
                text += " gateio" + " MISS!"
                print(err)
                pass
            text += "(Binance Announcement List " + i + " )"
            sendmsg(text)
            print(text)
        time.sleep(0.1)
