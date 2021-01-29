import os
import datetime
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
application = get_wsgi_application()

from core.models import (
    User,
    MonitorStock,
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
            return

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


class PriceDB:

    def __init__(self):
        print('Initializing PriceDB')

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


if __name__ == '__main__':
    user = UserDB('ppark9553@gmail.com')
    user.set_strategy('test_strategy')
    u = user.universe()
    # user.remove_from_universe(symbol='005930')
    print(user.universe())