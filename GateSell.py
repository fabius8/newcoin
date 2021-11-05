from bs4 import BeautifulSoup
import re
import time
import requests
import json
from datetime import datetime
import ccxt
import sys

coinlist = []
gateio = {}
config = json.load(open('config.json'))

if len(sys.argv) >= 2:
    for i in sys.argv[1:]:
        coinlist.append(i)
else:
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "No sell coin!")
    sys.exit(0)

def gateioInit(config):
    global gateio
    gateio["spot"] = ccxt.gateio(config["gate"])
    gateio["spot"].load_markets()

def gateioSell(coin, quantity, gateio):
    pair = coin + "_USDT"
    request = {
        'currency_pair': pair,
    }
    if coin + "/USDT" not in gateio["spot"].markets:
        print("Markets not have ", coin, "reload...")
        gateio["spot"].load_markets()
        return

    try:
        price = float(gateio["spot"].publicSpotGetOrderBook(request)['bids'][0][0])
    except Exception as e:
        #print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "can't get price", coin)
        pass
        return
    #print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), coin, "price:", price)
    if price * float(quantity) < 1:
        #print("too small")
        return
    time.sleep(120)
    print("sleep...")
    gateio["spot"].load_markets()
    price = float(gateio["spot"].publicSpotGetOrderBook(request)['bids'][0][0])
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

def getAccounts():
    request = {}
    accounts = gateio["spot"].privateSpotGetAccounts(request)
    return accounts

if __name__ == "__main__":
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Check", coinlist)
    gateioInit(config)
    while True:
        try:
            accounts = getAccounts()
            #print(accounts)
            for acc in accounts:
                if acc["currency"] in coinlist:
                    #print(acc)
                    #print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), acc["currency"], "Balance:", acc["available"])
                    try:
                        r = gateioSell(acc["currency"], acc["available"], gateio)
                        if r is not None:
                            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), r)
                    except exceptions as e:
                        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e)
                        pass
        except Exception as e:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e)
            pass
        time.sleep(3)
