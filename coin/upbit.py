import ccxt


class Upbit:

    def __init__(self, public_key=None, secret_key=None):
        if public_key is None and secret_key is None:
            self.api = ccxt.upbit({
                'apiKey': public_key,
                'secret': secret_key,
                'enableRateLimit': True
            })
        else:
            self.api = ccxt.upbit()
        self.markets = self.api.load_markets()

    def get_trading_tickers(self, currency='KRW'):
        # default로 원화로 구매가능한 코인 리스트를 리턴
        return [ticker for ticker in self.markets.keys() if currency in ticker]

    def get_ohlcv(self, symbol, timeframe='1m'):
        # 1분봉 데이터 리턴
        # 최대 200개 데이터 리턴 (limit=None으로 default 설정)
        return self.api.fetch_ohlcv(symbol, timeframe=timeframe)



if __name__ == '__main__':
    upbit = Upbit()
    print(upbit)