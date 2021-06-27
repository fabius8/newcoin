import json
import requests
import ccxt
import time

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
    print(r.json())

spreadR = 0.04
url = "https://api.thegraph.com/subgraphs/name/ethersphere/bzz-price-graph"
data =  "{\"variables\":{},\"query\":\"{\\n  ethPrices(first: 5) {\\n    price\\n    __typename\\n  }\\n  daiPrices(first: 5) {\\n    price\\n    __typename\\n  }\\n}\\n\"}"
okex_spot = ccxt.okex5(config["okex"])
okex_spot.load_markets()

while True:
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "START.....")
    try:
        r = requests.post(url, data = data)
        if r.ok:
            bzzprice = float(r.json()['data']['daiPrices'][0]['price'])/1000000000000000000
        else:
            time.sleep(30)
            print(r)
            continue
        
        okex_spot.load_markets()
        okexprice = float(okex_spot.fetch_order_book("BZZ/USDT")['asks'][0][0])
        
        print("bzzprice:", bzzprice)
        print("okexprice:", okexprice)
        spread = (okexprice - bzzprice) / bzzprice
        print(spread)
        if spread > spreadR:
            text = "bzzprice: " + str(bzzprice) + "\n"
            text += "okexprice: " + str(okexprice) + "\n"
            text += "okex price is more higher " + str(spread)
            sendmsg(text)
            time.sleep(60*5)
        if spread < -spreadR:
            text = "bzzprice: " + str(bzzprice) + "\n"
            text += "okexprice: " + str(okexprice) + "\n"
            text += "okex price is more lower " + str(spread)
            sendmsg(text)
            time.sleep(60*5)

    except Exception as err:
        print(err)
        sendmsg(str(err))
        time.sleep(30)
        pass
    print("\n")
    time.sleep(10)