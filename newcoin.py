import ccxt
import json
import time
import requests

config = json.load(open('config.json'))

secretjson = json.load(open('secret.json'))
corpid = secretjson["corpid"] 
corpsecret = secretjson["corpsecret"]

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
    print(r.url)
    print(r.json())

binance_spot = ccxt.binance(config["binance"])
okex_spot = ccxt.okex()
huobipro_spot = ccxt.huobipro()

binance_old_coin = []
binance_new_coin = []

okex_old_symbols = []
okex_symbols = []
huobipro_old_symbols = []
huobipro_symbols = []

count = 0

def init():
    binance_spot.load_markets()
    coininfo = binance_spot.sapiGetCapitalConfigGetall()
    for i in coininfo:
        binance_old_coin.append(i["coin"])

    okex_spot.load_markets()
    for symbol in okex_spot.markets:
        if "USDT" in symbol:
            okex_old_symbols.append(symbol)

    huobipro_spot.load_markets()
    for symbol in huobipro_spot.markets:
        if "USDT" in symbol:
            huobipro_old_symbols.append(symbol)

init()

while True:
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "START.....")
    time.sleep(5)
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "list coin count:", count)
    
    try:
        binance_spot.load_markets()
        coininfo = binance_spot.sapiGetCapitalConfigGetall()
        binance_new_coin = []
        for i in coininfo:
            binance_new_coin.append(i["coin"])

        coin_diff = list(set(binance_new_coin) - set(binance_old_coin))
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "binance", 
                "old coin count:", len(binance_old_coin),
                "new coin count:", len(binance_new_coin))

        if coin_diff:
            print(coin_diff)
            binance_old_coin = binance_new_coin
            count = count + 1
            text = "Binance list new coin: " + str(coin_diff)
            sendmsg(text)
        else:
            print("No new coin!")

    except Exception as err:
        print(err)
        sendmsg(err)
        pass

    try:
        okex_spot.load_markets()
        okex_symbols = []
        for symbol in okex_spot.markets:
            if "USDT" in symbol:
                okex_symbols.append(symbol)
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
        else:
            print("No new coin!")
    except Exception as err:
        print(err)
        sendmsg(err)
        pass

    try:
        huobipro_spot.load_markets()
        huobipro_symbols = []
        for symbol in huobipro_spot.markets:
            if "USDT" in symbol:
                huobipro_symbols.append(symbol)
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
        else:
            print("No new coin!")
    except Exception as err:
        print(err)
        sendmsg(err)
        pass


        
