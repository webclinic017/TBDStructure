import os
import sqlite3
import datetime
import pandas as pd
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
application = get_wsgi_application()

from core.models import (
    User,
    MonitorStock,
    Strategy,
    PortHistory,
    OHLCV,
)


class UserDB:

    def __init__(self, email):
        self.user = User.objects.filter(email=email).first()
        self.id = self.user.id
        self.today = datetime.datetime.now().strftime('%Y%m%d')

        self.strategy = None

    def _check_strategy_name_present(self, strategy):
        if strategy is None:
            if self.strategy is not None:
                strategy = self.strategy
            else:
                raise Exception('전략 이름을 정해주세요.')
        return strategy

    def set_strategy(self, strategy):
        self.strategy = strategy

    def save_strategy(self, strategy_name=None, account_num=None, using_strategy=None, source=None, server_type=None, capital=None, currency=None):
        """
        모든 전략에는 전략명과 사용 전략을 명시해줘야 한다.

        strategy_name은 본인이 지은 전략의 이름이고,
        using_strategy는 사용하는 전략의 이름이다.

        strategy_name은 unique한 값이라고 가정한다.
        """
        strategy = self._check_strategy_name_present(strategy_name)

        strategy_obj = Strategy.objects.filter(strategy_name=self.strategy)
        if len(strategy_obj) == 0:
            # 아직 DB에 정보가 없다면 새로 생성하여 준다.
            # save_strategy만 하면 생성 혹은 업데이트를 할 수 있다.
            s = Strategy(
                user=self.user,
                account_num=account_num,
                strategy_name=strategy,
                using_strategy=using_strategy,
                source=source,
                server_type=server_type,
                capital=capital if capital is not None else 1000000,
                currency=currency if currency is not None else 'KRW'
            )
            s.save()
        else:
            # 이미 데이터가 존재한다면 업데이트를 한다.
            update_data = {
                'account_num': account_num,
                'using_strategy': using_strategy,
                'source': source,
                'server_type': server_type,
                'capital': capital,
                'currency': currency
            }
            update_data = {key: val for key, val in update_data.items() if val is not None}
            strategy_obj.update(**update_data)

    def get_strategy(self, strategy=None) -> dict:
        """
        전략 정보가 없다면 만들어서 기본값으로 만들어 리턴하고, 있다면 object를 리턴하는 형식
        """
        strategy = self._check_strategy_name_present(strategy)
        strategy_obj = Strategy.objects.filter(strategy_name=strategy)
        if len(strategy_obj) == 0:
            # 아직 정보가 없다면 오류를 raise하지 않고 save_strategy를 통하여 default값으로 인스턴스를 생성한다.
            self.save_strategy()
        return Strategy.objects.filter(strategy_name=self.strategy).values().first()

    def remove_strategy_from_db(self, strategy):
        MonitorStock.objects.filter(user=self.user, strategy=strategy).delete()
        PortHistory.objects.filter(user=self.user, strategy=strategy).delete()

    def universe(self, strategy: str = None, date=None):
        strategy = self._check_strategy_name_present(strategy)

        if date is None:
            date = self.today

        m = self.user.monitorstock.filter(strategy=strategy, date=date).first()
        if m is not None:
            return m.codelist.split(';')
        else:
            return []

    def add_to_universe(self, strategy: str = None, symbol: str or list = None):
        strategy = self._check_strategy_name_present(strategy)

        if symbol is None:
            raise Exception('저장하고 싶은 종목명을 스트링 혹은 리스트로 제공해주세요.')

        if type(symbol) == list:
            symbol = ';'.join(symbol)

        if self.user.monitorstock.filter(strategy=strategy, date=self.today).count() == 0:
            m = MonitorStock(
                user=self.user,
                strategy=strategy,
                date=self.today,
                codelist=symbol
            )
            m.save()
        else:
            m = self.user.monitorstock.filter(strategy=strategy, date=self.today).first()
            m.codelist = f'{m.codelist};{symbol}'
            m.save()

    def remove_from_universe(self, strategy: str = None, symbol: str or list = None):
        strategy = self._check_strategy_name_present(strategy)

        if symbol is None:
            raise Exception('저장하고 싶은 종목명을 스트링 혹은 리스트로 제공해주세요.')

        if self.user.monitorstock.filter(strategy=strategy, date=self.today).count() == 0:
            return False
        else:
            m = self.user.monitorstock.filter(strategy=strategy, date=self.today).first()
            codelist = m.codelist.split(';')
            if type(symbol) == str:
                if symbol in codelist:
                    codelist.remove(symbol)
            elif type(symbol) == list:
                codelist = list(set(codelist).difference(set(symbol)))
            m.codelist = ';'.join(codelist)
            m.save()

    def get_porthistory(self, strategy: str = None):
        strategy = self._check_strategy_name_present(strategy)
        history = self.user.history.filter(strategy=strategy).values().all()
        return history

    def add_porthistory(self, date, traded_stock, traded_time, action, amount, price, strategy: str = None):
        strategy = self._check_strategy_name_present(strategy)
        h = PortHistory(
            user=self.id,
            strategy=strategy,
            date=date,
            traded_stock=traded_stock,
            traded_time=traded_time,
            action=action,
            amount=amount,
            price=price
        )
        h.save()


class PriceDB:

    def __init__(self):
        """
        Django 모델을 통해서 정의내린 테이블로 엑세스하여 데이터를 가져올 수 있다.

        table명을 확인하는 방법: SELECT name FROM sqlite_master WHERE type='table';
        """
        print('Initializing PriceDB')
        self.conn = sqlite3.connect('db.sqlite3')

    def save_minute_data(self, code: str, data: list):
        print(f'Saving {code} data to DB')
        existing_dates_in_db = OHLCV.objects.filter(code=code)\
                                            .values_list('date', flat=True)
        existing_dates_in_db = list(set(existing_dates_in_db))
        p_d = []
        for d in data:
            # DB에 없는 데이터만 저장하기
            if str(d['date']) not in existing_dates_in_db: 
                p_d.append(OHLCV(
                    code=str(d['code']),
                    date=str(d['date']),
                    open_prc=int(d['open']),
                    high_prc=int(d['high']),
                    low_prc=int(d['low']),
                    close_prc=int(d['close']),
                    volume=int(d['volume'])
                ))
        OHLCV.objects.bulk_create(p_d)
        print(f'Save Complete. Saved: {len(p_d)} data pts.')

    def get_minute_data(self, code: str or list, pivot=False, pivot_on='close_prc'):
        if type(code) == str:
            code_query = f"'{code}'"
        elif type(code) == list:
            code_query = ','.join([f"'{c}'" for c in code])

        df = pd.read_sql(f"""
        SELECT code, date, open_prc, high_prc, low_prc, close_prc, volume
        FROM core_ohlcv WHERE code IN ({code_query});
        """, self.conn)

        if pivot:
            return pd.pivot_table(df, values='close_prc', index='date', columns='code')
        else:
            return df


if __name__ == '__main__':
    # monitor stocks (universe) 설정하는 방법
    user = UserDB('ppark9553@gmail.com')
    user.set_strategy('test_strategy')
    u = user.universe()
    # user.remove_from_universe(symbol='005930')
    print(user.universe())

    # 가격 정보를 가져오는 방법 + pivot_table 만드는 방법
    db = PriceDB()
    price = db.get_minute_data(['005930', '000020', '066570'], pivot=True)
    print(price)