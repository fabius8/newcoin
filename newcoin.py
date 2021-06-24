import ccxt
import json
import time
import requests
import sys
from bs4 import BeautifulSoup
import re

config = json.load(open('config.json'))

secretjson = json.load(open('secret.json'))
corpid = secretjson["corpid"] 
corpsecret = secretjson["corpsecret"]

errorCount = 0

def sendmsg(text):
    params = {
        "corpid": corpid,
        "corpsecret": corpsecret
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
    print(r.json())



binance_spot = ccxt.binance(config["binance"])
binance_spot.load_markets()
okex_spot = ccxt.okex5(config["okex"])
okex_spot.load_markets()
huobipro_spot = ccxt.huobipro(config["huobi"])
huobipro_spot.load_markets()

binance_old_coin = []
binance_new_coin = []

okex_old_symbols = []
okex_symbols = []
huobipro_old_symbols = []
huobipro_symbols = []

count = 0

def trade_binance(coin, exchange):
    pair = coin + "/USDT"
    for symbol in exchange.markets:
        if pair == symbol:
            print(exchange, " has new coin list: ", pair)
            price = exchange.fetch_order_book(pair)['asks'][0][0]
            account = exchange.private_get_account()
            usdamount = 0
            for item in account["balances"]:
                if item["asset"] == "USDT":
                    usdamount = item["free"]
            maxBuyAmount = int(float(usdamount) / float(price) * 0.8)
                    
            print(price, maxBuyAmount)
            exchange.createMarketBuyOrder(pair, maxBuyAmount)
            text = str(exchange) + "buy" + pair + str(maxBuyAmount) + "on" + str(price)
            sendmsg(text)
            return True
    text = str(exchange) + "miss"
    sendmsg(text)
    return False

def trade_okex(coin, exchange):
    pair = coin + "-USDT"
    for symbol in exchange.markets:
        if pair in symbol:
            print(exchange, "has new coin list: ", pair)
            maxSize = exchange.private_get_account_max_size({"instId": pair, "tdMode": "cash"})
            maxBuyAmount = float(maxSize["data"][0]["maxBuy"])
            if maxBuyAmount > 0:
                exchange.private_post_trade_order({
                    "instId": pair,
                    "tdMode":"cash",
                    "side":"buy",
                    "ordType":"market",
                    "sz": str(maxBuyAmount * 0.8)
                })
            text = str(exchange) + "buy" + pair + str(maxBuyAmount)
            sendmsg(text)
            return True
    text = str(exchange) + "miss"
    sendmsg(text)
    return False

def trade_huobi(coin, exchange):
    pair = coin + "/USDT"
    for symbol in exchange.markets:
        #print(symbol)
        if pair in symbol:
            print(exchange, "has new coin list: ", pair)
            price = exchange.fetch_order_book(pair)['asks'][0][0]
            account_id = exchange.private_get_account_accounts()
            id = 0
            for item in account_id["data"]:
                if "spot" == item["type"]:
                    id = item["id"]
            balance = exchange.private_get_account_accounts_id_balance({"id": id})
            usdamount = 0
            for item in balance["data"]["list"]:
                if "usdt" in item["currency"] and item["type"] == "trade":
                    usdamount = item["balance"]
            maxBuyAmount = int(float(usdamount) / float(price) * 0.8)
            exchange.createMarketBuyOrder(pair, maxBuyAmount)
            text = str(exchange) + "buy" + pair + str(maxBuyAmount) + "on" + str(price)
            sendmsg(text)
            return True
    text = str(exchange) + "miss"
    sendmsg(text)
    return False

def getBinanceAnnCoin():
    r = requests.get("https://www.binance.com/en/support/announcement")
    soup = BeautifulSoup(r.text, "html.parser")
    data = soup.find(id="__APP_DATA")
    i = json.loads(data.string)["routeProps"]["42b1"]["catalogs"][0]
    for item in i["articles"]:
        print(item)
        info = re.search(r'.* Will List .*\((.*)\)', str(item), re.I)
        if info:
            print(info.group(1))
            return info.group(1)
    return None



#init
coininfo = binance_spot.sapiGetCapitalConfigGetall()
for i in coininfo:
    binance_old_coin.append(i["coin"])
    
coininfo = okex_spot.private_get_asset_currencies()
for i in coininfo["data"]:
    okex_old_symbols.append(i["ccy"])
  
coininfo = huobipro_spot.public_get_common_currencys()
huobipro_old_symbols = coininfo["data"]


while True:
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "START.....")
    time.sleep(5)
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "list new coin count:", count, "error: ", errorCount)
    # BINANCE
    try:
        binance_spot.load_markets()
        coininfo = binance_spot.sapiGetCapitalConfigGetall()
        binance_new_coin = []
        for i in coininfo:
            binance_new_coin.append(i["coin"])
        BAnncoin = getBinanceAnnCoin()
        if BAnncoin and BAnncoin not in binance_new_coin:
            text = "Binance announcement new coin!" + str(BAnncoin) + "!"
            binance_new_coin.append(BAnncoin)
        coin_diff = list(set(binance_new_coin) - set(binance_old_coin))
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "binance", 
                "old coin count:", len(binance_old_coin),
                "new coin count:", len(binance_new_coin))

        if coin_diff:
            print(coin_diff)
            binance_old_coin = binance_new_coin
            count = count + 1
            text += "Binance list new coin: " + str(coin_diff)
            sendmsg(text)
            trade_okex(coin_diff[0], okex_spot)
            trade_huobi(coin_diff[0], huobipro_spot)
        else:
            print("No new coin!")

    except Exception as err:
        print(err)
        if errorCount < 2:
            sendmsg(str(err))
            errorCount += 1
        pass

    # OKEX
    try:
        okex_spot.load_markets()
        coininfo = okex_spot.private_get_asset_currencies()
        okex_symbols = []
        for i in coininfo["data"]:
            okex_symbols.append(i["ccy"])

        diff = list(set(okex_symbols) - set(okex_old_symbols))
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "okex", 
                "old count:", len(okex_old_symbols),
                "new count:", len(okex_symbols))
        if diff:
            print(diff, len(diff))
            okex_old_symbols = okex_symbols
            count = count + 1
            text = "OKEX" + "List New Coin!" + str(diff)
            sendmsg(text)
            trade_binance(diff[0], binance_spot)
            trade_huobi(diff[0], huobipro_spot)
        else:
            print("No new coin!")
    except Exception as err:
        print(err)
        if errorCount < 2:
            sendmsg(str(err))
            errorCount += 1
        pass

    # HUOBI
    try:
        huobipro_spot.load_markets()
        coininfo = huobipro_spot.public_get_common_currencys()
        huobipro_symbols = list(coininfo["data"])

        diff = list(set(huobipro_symbols) - set(huobipro_old_symbols))
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "huobipro", 
                "old count:", len(huobipro_old_symbols),
                "new count:", len(huobipro_symbols))
        if diff:
            print(diff, len(diff))
            huobipro_old_symbols = huobipro_symbols
            count = count + 1
            text = "huobipro" + "List New Coin!" + str(diff)
            sendmsg(text)
            trade_binance(diff[0], binance_spot)
            trade_okex(diff[0], okex_spot)
        else:
            print("No new coin!")
    except Exception as err:
        print(err)
        if errorCount < 2:
            sendmsg(str(err))
            errorCount += 1
        pass


        
