from datetime import datetime, timedelta
import time, json, calendar
import cbpro
#Credentials
key = '8da2e3ada96a6fee893ad8750e0f341d'
secret = 'JS/IioxL15Lg3liGWYMiHAOF8ZFXq1ie6met1ed1++T61ImuJeo93Sjk7S2xkQ8LCmDDq36hRYz2FcuChp/HSw=='
passphrase = 'k8f4r1czu8s'
sandbox = 'https://api-public.sandbox.pro.coinbase.com'
#Clients
messenger = cbpro.Messenger()
public = cbpro.PublicClient(messenger)

private = cbpro.private_client(key, secret, passphrase, sandbox)

activeSymbols = [] 

def get_all_symbols():
    time.sleep(0.26)
    symbols = [] 
    products = public.products.list()
    for product in products:
        symbol = (product['id'])
        if 'USD' in symbol and 'USDC' not in symbol and 'USDT' not in symbol:
            symbols.append(symbol)
        else:
            pass

    return symbols

def getCurrentPrice(symbol):
    time.sleep(0.26)
    priceDict = public.products.stats(symbol)
    price = priceDict['last']
    return price 

def check_watch_list(symbol, currentPrice):
    try:
        currentTime = datetime.now()
        timeData = currentTime + timedelta(days = -60)
        start = timeData.strftime("%Y-%m-%dT") + '00:00:00'
        granularity = 60

        params = {'start': start, 'end': start, 'granularity': granularity} 
        history = public.products.history(symbol, params)
        time.sleep(0.26)

        product_id = symbol # 'BTC-USD'

        priceCheck = history[0][3]

        difference = abs(1 - (float(currentPrice) / float(priceCheck)))
        

        if difference > 0.5:
            status = False
        elif difference < 0.5:
            status = True

        print('-------------')
        print(symbol)
        print(difference)
        print(currentPrice)
        print(priceCheck)
        print(status)
        print('-------------')

        return status
    
    except:
        print(symbol)
        print("isWatch Check Failed -  - Historical Data not found from Coinbase")
        return False

def check_flat(symbol, currentPrice):
    try:
        status = False

        currentTime = datetime.now()
        timeData = currentTime + timedelta(days = -2)
        start = timeData.strftime("%Y-%m-%dT") + '00:00:00'

        granularity = 60

        params = {'start': start, 'end': start, 'granularity': granularity} 
        history = public.products.history(symbol, params)
        time.sleep(0.26)

        priceCheck = history[0][3]

        difference = abs(1 - (float(priceCheck) / float(currentPrice)))

        if difference > 0.01:
            status = False
        elif difference < 0.01:
            status = True

        print('-------------')
        print(symbol)
        print(difference)
        print(currentPrice)
        print(priceCheck)
        print(status)
        print('-------------')

        return status
        

    except:
        print(symbol)
        print("isFlat Check Failed - Historical Data not found from Coinbase")
        return False

def buy(symbol, amount):
    market = {
        'funds': amount, # may need to have decimal
        'side': 'buy',
        'product_id': symbol,
        'type': 'market',
    }
    response = private.orders.post(market)
    print(response)

def sell(symbol, size):
    market = {
        'size': size, # may need to have decimal
        'side': 'sell',
        'product_id': symbol,
        'type': 'market',
    }
    response = private.orders.post(market)
    print(response)

def get_active_wallets():
    activeWallets = []
    activeSymbols = []
    wallets = private.accounts.list() 
    time.sleep(0.25)
    
    for wallet in wallets:
        balance = float(wallet.get('balance'))
        if balance > 0:
            size = wallet.get('available')
            symbol = wallet.get('currency')
            activeSymbols.append(symbol + '-USD')
            activeWallet = {'symbol': symbol, 'price': balance, 'size': size}
            activeWallets.append(activeWallet)

    return activeWallets, activeSymbols
            
def filter_fill_data(symbol):
    filteredFills = [] 
    product_id = {'product_id': symbol}
    fills = private.fills.list(product_id)
    for fill in fills:# {'created_at': '2021-05-22T19:45:15.07Z', 'trade_id': 29912427, 'product_id': 'BTC-USD', 'order_id': 'fc68d9c7-662c-435a-8e07-152fb9c3927e', 'user_id': '5d0c40c934ae30321551b72f', 'profile_id': '867ccf0a-6475-43ae-95ce-fe0bcf2316ea', 'liquidity': 'T', 'price': '37915.85000000', 'size': '0.00210487', 'fee': '0.3990396759475000', 'side': 'buy', 'settled': True, 'usd_volume': '79.8079351895000000'}
        timedata = fill.get('created_at')
        time = calendar.timegm(datetime.strptime(timedata, "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
        symbol = fill.get('product_id')
        price = fill.get('price')
        size = fill.get('size')
        side = fill.get('side')

        if side == 'buy':
            filteredFills.append([time, symbol, price, size])
            
    recentFills = []
    usedSymbols = []
    for item in filteredFills: 
        if item[1] not in usedSymbols:
            recentFills.append(item)
            usedSymbols.append(item[1])

    return recentFills[0]

def check_sell_condition(symbols: list):
    currentSymbols = []
    message = cbpro.get_message({
    'type': 'subscribe',
    'product_ids': symbols, 
    'channels': ['ticker']
    })

    header = cbpro.WebsocketHeader(key, secret, passphrase)
    stream = cbpro.WebsocketStream(header=header, traceable=False)

    stream.connect()
    stream.send(message)

    time.sleep(1)

    for symbol in range(len(symbols) + 1):
        response = stream.receive()
        symbol = response.get('product_id')
        price = response.get('price')
        item = {'symbol': symbol, "price": price}

        if str(symbol) in symbols:
            currentSymbols.append(item)
        else:
            pass

        time.sleep(0.5)

    stream.disconnect()

    for j in currentSymbols:
        marketSymbol = j.get('symbol')
        price = j.get("price")
        fillData = filter_fill_data(marketSymbol) # [1621869301, 'BTC-USD', '37672.65000000', '0.00264123']
        priceDifference = float(fillData[2]) - float(price)

        valueChange = priceDifference - float(fillData[2])

        if valueChange > 0.05:
            print(f'SELL {marketSymbol}')
            sell(marketSymbol, fillData[3])
            time.sleep(0.26)
        else:
            continue

def main():
    start = time.time()
    print('starting...')
    optimalTrades = []
    symbols = get_all_symbols()
    activeWallets, activeSymbols = get_active_wallets()
    check_sell_condition(activeSymbols)
    for symbol in symbols:
        currentPrice = getCurrentPrice(symbol)
        isFlat = check_flat(symbol, currentPrice)

        if isFlat == True:
            isWatch = check_watch_list(symbol, currentPrice)
        else:
            continue

        if isFlat == True and isWatch == True:
            if symbol not in activeSymbols:
                print(f"BUY {symbol}")
                buy(symbol, '200')

    print(f'Time to complete: {time.time() - start}')


# main()