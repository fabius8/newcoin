import ccxt
import json
import time
import requests
import sys
from bs4 import BeautifulSoup
import re
import logging
logging.basicConfig(level=logging.INFO,
                    filename='output.log',
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

config = json.load(open('config.json'))

secretjson = json.load(open('secret.json'))
corpid = secretjson["corpid"] 
corpsecret = secretjson["corpsecret"]

errorCount = 0
ratio = 0.8

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
    logging.info(r.json())



binance_spot = ccxt.binance(config["binance"])
binance_spot.load_markets()
okex_spot = ccxt.okex5(config["okex"])
okex_spot.load_markets()
huobipro_spot = ccxt.huobipro(config["huobi"])
huobipro_spot.load_markets()

def getAllbalance(binance, okex, huobipro):
    # binance
    account = binance.private_get_account()
    for item in account["balances"]:
        if item["asset"] == "USDT":
            logging.info("%s: USDT %s", binance, item["free"])
            break
    # okex
    account = okex.private_get_account_balance({"ccy": "USDT"})
    balance = account["data"][0]["details"][0]["availEq"]
    logging.info("%s: USDT %s", okex, balance)
    # huobi
    account_id = huobipro.private_get_account_accounts()
    id = 0
    for item in account_id["data"]:
        if "spot" == item["type"]:
            id = item["id"]
    balance = huobipro.private_get_account_accounts_id_balance({"id": id})
    for item in balance["data"]["list"]:
        if "usdt" in item["currency"] and item["type"] == "trade":
            logging.info("%s: USDT %s", huobipro, item["balance"])  
            break 

getAllbalance(binance_spot, okex_spot, huobipro_spot)

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
            logging.info("%s has new coinlist: %s", exchange, pair)
            price = exchange.fetch_order_book(pair)['asks'][0][0]
            account = exchange.private_get_account()
            usdamount = 0
            for item in account["balances"]:
                if item["asset"] == "USDT":
                    usdamount = item["free"]
            maxBuyAmount = int(float(usdamount) / float(price) * ratio)
                    
            logging.info("%s %s", price, maxBuyAmount)
            exchange.createMarketBuyOrder(pair, maxBuyAmount)
            text = str(exchange) + "buy" + pair + str(maxBuyAmount) + "on" + str(price)
            sendmsg(text)
            return True
    text = str(exchange) + " miss"
    sendmsg(text)
    return False

def trade_okex(coin, exchange):
    pair = coin + "-USDT"
    for symbol in exchange.markets:
        if pair in symbol:
            logging.info("%s has new coinlist: %s", exchange, pair)
            maxSize = exchange.private_get_account_max_size({"instId": pair, "tdMode": "cash"})
            maxBuyAmount = float(maxSize["data"][0]["maxBuy"])
            if maxBuyAmount > 0:
                exchange.private_post_trade_order({
                    "instId": pair,
                    "tdMode":"cash",
                    "side":"buy",
                    "ordType":"market",
                    "sz": str(maxBuyAmount * ratio)
                })
            text = str(exchange) + "buy" + pair + str(maxBuyAmount)
            sendmsg(text)
            return True
    text = str(exchange) + " miss"
    sendmsg(text)
    return False

def trade_huobi(coin, exchange):
    pair = coin + "/USDT"
    for symbol in exchange.markets:
        if pair in symbol:
            logging.info("%s has new coin list: %s", exchange, pair)
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
            maxBuyAmount = int(float(usdamount) * ratio)
            exchange.createMarketBuyOrder(pair, maxBuyAmount)
            text = str(exchange) + "buy " + pair + str(maxBuyAmount) + "on " + str(price)
            sendmsg(text)          
            return True
    text = str(exchange) + " miss"
    sendmsg(text)
    return False

def getBinanceAnnCoin():
    r = requests.get("https://www.binance.com/en/support/announcement")
    soup = BeautifulSoup(r.text, "html.parser")
    data = soup.find(id="__APP_DATA")
    i = json.loads(data.string)["routeProps"]["42b1"]["catalogs"][0]
    for item in i["articles"]:
        info = re.search(r'.* Will List .*\((.*)\)', str(item), re.I)
        if info:
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
    print("START.....")
    time.sleep(5)
    print("list new coin count: ", count, "err:", errorCount)
    # BINANCE
    try:
        binance_spot.load_markets()
        coininfo = binance_spot.sapiGetCapitalConfigGetall()
        binance_new_coin = []
        text = ""
        for i in coininfo:
            binance_new_coin.append(i["coin"])
        BAnncoin = getBinanceAnnCoin()
        if BAnncoin and BAnncoin not in binance_new_coin:
            text += "Binance announcement new coin!" + str(BAnncoin) + "!"
            binance_new_coin.append(BAnncoin)
        coin_diff = list(set(binance_new_coin) - set(binance_old_coin))
        print(
                "binance", 
                "old coin count:", len(binance_old_coin),
                "new coin count:", len(binance_new_coin))

        if coin_diff:
            logging.info(coin_diff)
            binance_old_coin = binance_new_coin
            count = count + 1
            text += "Binance list new coin: " + str(coin_diff)
            sendmsg(text)
            trade_okex(coin_diff[0], okex_spot)
            trade_huobi(coin_diff[0], huobipro_spot)
        else:
            print("No new coin!")

    except Exception as err:
        if "binance GET https:" in str(err):
            logging.error("Time out")
        else:
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
        print(
                "okex", 
                "old count:", len(okex_old_symbols),
                "new count:", len(okex_symbols))
        if diff:
            logging.info("%s %s", diff, len(diff))
            okex_old_symbols = okex_symbols
            count = count + 1
            text = "OKEX" + "List New Coin!" + str(diff)
            sendmsg(text)
            trade_binance(diff[0], binance_spot)
            trade_huobi(diff[0], huobipro_spot)
        else:
            print("No new coin!")
    except Exception as err:
        logging.error(err)
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
        print("huobipro", 
                "old count:", len(huobipro_old_symbols),
                "new count:", len(huobipro_symbols))
        if diff:
            logging.info("%s %s", diff, len(diff))
            huobipro_old_symbols = huobipro_symbols
            count = count + 1
            text = "huobipro" + "List New Coin!" + str(diff)
            sendmsg(text)
            trade_binance(diff[0], binance_spot)
            trade_okex(diff[0], okex_spot)
        else:
            print("No new coin!")
    except Exception as err:
        logging.error(err)
        if errorCount < 2:
            sendmsg(str(err))
            errorCount += 1
        pass


        
