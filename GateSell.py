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

def coinlistInit():
    global coinlist
    f = open("coinlist.txt")
    lines = f.readlines()
    tmp = []
    for line in lines:
        line = line.strip('\n')
        line = line.split(" ")
        for i in line:
            if i == "":
                continue
            tmp.append(i)
    if tmp != coinlist:
        coinlist = tmp
        print("coinlist:", coinlist)
    f.close()


    

if len(sys.argv) >= 2:
    config = json.load(open(sys.argv[1]))
else:
    config = json.load(open('config.json'))

print(config["gate"]["name"])

def gateioInit(config):
    global gateio
    gateio["spot"] = ccxt.gateio(config["gate"])
    gateio["spot"].load_markets()

# gate buy
def gateioBuy(coin, gateio):
    gateio["spot"].load_markets()
    usdtQuantity = 100
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

def gateioSell(coin, quantity, gateio):
    pair = coin + "_USDT"
    request = {
        'currency_pair': pair,
    }
    if coin + "/USDT" not in gateio["spot"].markets:
        #print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Markets not have ", coin, "reload...")
        gateio["spot"] = ccxt.gateio(config["gate"])
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
   
    print("wait 70s to sell ...")
    time.sleep(70)
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
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e, "44")
        pass
        return
    return request

def getAccounts():
    request = {}
    try:
        accounts = gateio["spot"].privateSpotGetAccounts(request)
    except Exception as e:
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e, "getAccounts")
        pass
    return accounts

if __name__ == "__main__":
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "start...")
    coinlistInit()
    gateioInit(config)
    while True:
        try:
            coinlistInit()
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
                        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e, "33")
                        pass
        except Exception as e:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e, "22")
            pass
        time.sleep(3)
