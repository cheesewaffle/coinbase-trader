from datetime import datetime, timedelta
import time
import json
import calendar
import config
import cbpro

# Credentials
key = config.key
secret = config.secret
passphrase = config.passphrase
sandbox = config.sandbox

# Clients
messenger = cbpro.Messenger()
public = cbpro.PublicClient(messenger)
private = cbpro.private_client(key, secret, passphrase, sandbox)

activeSymbols = []

def get_all_symbols():  # Grabs all symbols from coinbase
    time.sleep(0.26)
    symbols = []
    products = public.products.list()
    for product in products:
        symbol = (product['id'])
        if 'USD' in symbol and 'USDC' not in symbol and 'USDT' not in symbol and 'DAI' not in symbol:
            symbols.append(symbol)

    return symbols

def getCurrentPrice(symbol):  # Grabs current price for symbol
    time.sleep(0.26)
    priceDict = public.products.stats(symbol)
    price = priceDict['last']
    return price

def check_watch_list(symbol, currentPrice):  # 60 Day - check if 50% decrease
    try:
        currentTime = datetime.now()
        timeData = currentTime + timedelta(hours=-1435) # Timezone offset factored in -5 hours
        requestedTime = timeData.strftime("%Y-%m-%dT%H:%M:00")

        params = {'start': requestedTime,
                  'end': requestedTime, 'granularity': 60}
        history = public.products.history(symbol, params)
        time.sleep(0.26)

        priceCheck = history[0][3]

        difference = abs(1 - (float(currentPrice) / float(priceCheck)))

        if difference > 0.5:
            status = False
            print(f'{symbol} not watch...')
        elif difference < 0.5:
            status = True
            print('-------------')
            print(
                f'CheckWatch\nSymbol: {symbol}\nDifference: {difference}\nCurrent Price: {currentPrice}\nPrice Check: {priceCheck}\nStatus: {status}\nHistory: {history}')
            print('-------------')

        return status

    except:
        print(
            f"{symbol}\nisWatch Check Failed -  - Historical Data not found from Coinbase")
        return False

def check_flat(symbol, currentPrice):  # 48 Hour - check if withing 1%
    try:
        status = False
        currentTime = datetime.now()
        timeData = currentTime + timedelta(hours=-43) # Timezone offset factored in -5 hours 
        requestedTime = timeData.strftime("%Y-%m-%dT%H:%M:00")

        params = {'start': requestedTime,
                  'end': requestedTime, 'granularity': 60}
        history = public.products.history(symbol, params)
        time.sleep(0.26)

        priceCheck = history[0][3]

        difference = abs(1 - (float(priceCheck) / float(currentPrice)))

        if difference > 0.01:
            status = False
            print(f'{symbol} not flat...')
        elif difference < 0.01:
            status = True
            print('-------------')
            print(
                f'CheckFlat\nSymbol: {symbol}\nDifference: {difference}\nCurrent Price: {currentPrice}\nPrice Check: {priceCheck}\nStatus: {status}')
            print('-------------')

        return status

    except:
        print(
            f"{symbol}\nisFlat Check Failed - Historical Data not found from Coinbase")
        return False

def buy(symbol, amount):  # Buy at market price
    market = {
        'funds': amount,  # may need to have decimal
        'side': 'buy',
        'product_id': symbol,
        'type': 'market',
    }
    response = private.orders.post(market)
    print(response)

def sell(symbol, size):  # Sell at market price
    market = {
        'size': size,  # may need to have decimal
        'side': 'sell',
        'product_id': symbol,
        'type': 'market',
    }
    response = private.orders.post(market)
    print(response)

def get_active_wallets():  # Grabs all wallets from account that are a USD pair
    activeWallets, activeSymbols = [], []
    wallets = private.accounts.list()
    time.sleep(0.26)

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
    for fill in fills:  # {'created_at': '2021-05-22T19:45:15.07Z', 'trade_id': 29912427, 'product_id': 'BTC-USD', 'order_id': 'fc68d9c7-662c-435a-8e07-152fb9c3927e', 'user_id': '5d0c40c934ae30321551b72f', 'profile_id': '867ccf0a-6475-43ae-95ce-fe0bcf2316ea', 'liquidity': 'T', 'price': '37915.85000000', 'size': '0.00210487', 'fee': '0.3990396759475000', 'side': 'buy', 'settled': True, 'usd_volume': '79.8079351895000000'}
        timedata = fill.get('created_at')
        time = calendar.timegm(datetime.strptime(
            timedata, "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())
        symbol = fill.get('product_id')
        price = fill.get('price')
        size = fill.get('size')
        side = fill.get('side')

        if side == 'buy':
            filteredFills.append([time, symbol, price, size])

    recentFills, usedSymbols = [], []

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
        print(j)
        marketSymbol = j.get('symbol')
        price = j.get("price")
        # [1621869301, 'BTC-USD', '37672.65000000', '0.00264123']
        fillData = filter_fill_data(marketSymbol)
        priceDifference = float(fillData[2]) - float(price)

        valueChange = abs(float(fillData[2])) - abs(priceDifference)

        print(f"fillData: {float(fillData[2])}")
        print(f"price: {price}")
        print(f"priceDifference: {priceDifference}")
        print(f"valuechange: {valueChange}")

        if valueChange > 0.05:
            print(f'SELL {marketSymbol}')
            sell(marketSymbol, fillData[3])
            time.sleep(0.26)
        else:
            continue

def main():
    archive = []
    start = time.time()
    print('starting...')
    optimalTrades = []
    symbols = get_all_symbols()
    activeWallets, activeSymbols = get_active_wallets()
    check_sell_condition(activeSymbols) # check this 
    for symbol in symbols:
        isWatch, isFlat = False, False
        currentPrice = getCurrentPrice(symbol)
        isFlat = check_flat(symbol, currentPrice)

        if isFlat == True:
            isWatch = check_watch_list(symbol, currentPrice)

        if isFlat == True and isWatch == True:
            if symbol not in activeSymbols:
                print(f"BUY {symbol}")
                buy(symbol, '200')
                archive.append([symbol, currentPrice, isFlat, isWatch])
        
    print(archive)
    print(f'Time to complete: {time.time() - start}')

main()
