import ccxt
import json
import time
import requests

secretjson = json.load(open('secret.json'))
secret = secretjson["secret"] 
url = 'https://sctapi.ftqq.com/' + secret + '.send'
data = {'title':'NULL','desp':'NULL'}

binance_spot = ccxt.binance()
okex_spot = ccxt.okex()
huobipro_spot = ccxt.huobipro()

binance_old_symbols = []
binance_symbols = []
okex_old_symbols = []
okex_symbols = []
huobipro_old_symbols = []
huobipro_symbols = []

count = 0

while True:
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "START.....", )
    time.sleep(3)
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "list coin count:", count)
    try:
        binance_spot.load_markets()
        for symbol in binance_spot.markets:
            if "USDT" in symbol:
                binance_symbols.append(symbol)
        diff = list(set(binance_symbols) - set(binance_old_symbols))
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "binance", 
                "old count:", len(binance_old_symbols),
                "new count:", len(binance_symbols))
        if diff:
            print(diff, len(diff))
            binance_old_symbols = binance_symbols
            if len(diff) > 10:
                binance_symbols = []
                continue
            count = count + 1
            data['title'] = "Binance" + "List New Coin!"
            data['desp'] = '.'.join(diff)
            r = requests.post(url, data)
            print("send message")
        else:
            print("No new coin!")
        binance_symbols = []
    except Exception as err:
        print(err)
        data['title'] = "Error"
        data['desp'] = err
        r = requests.post(url, data)
        pass

    try:
        okex_spot.load_markets()
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
            if len(diff) > 10:
                okex_symbols = []
                continue
            count = count + 1
            data['title'] = "OKEX" + "List New Coin!"
            data['desp'] = '.'.join(diff)
            r = requests.post(url, data)
            print("send message")
        else:
            print("No new coin!")
        okex_symbols = []
    except Exception as err:
        print(err)
        data['title'] = "Error"
        data['desp'] = err
        r = requests.post(url, data)
        pass

    try:
        huobipro_spot.load_markets()
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
            if len(diff) > 10:
                huobipro_symbols = []
                continue
            count = count + 1
            data['title'] = "huobipro" + "List New Coin!"
            data['desp'] = '.'.join(diff)
            r = requests.post(url, data)
            print("send message")
        else:
            print("No new coin!")
        huobipro_symbols = []
    except Exception as err:
        print(err)
        data['title'] = "Error"
        data['desp'] = err
        r = requests.post(url, data)
        pass


        
