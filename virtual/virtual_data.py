import os
import time
import pandas as pd

trade_cols = [
    'code',
    'trade_date',
    'timestamp',
    'current_price',
    'open_price',
    'high',
    'low',
    'volume',
    'cum_volume',
    'trade_sell_hoga1',
    'trade_buy_hoga1',
    'rotation',
    'strength',
    'mkt_type',
    'mkt_cap'
]

orderbook_cols = [
    'code',
    'hoga_date',
    'timestamp',
    'sell_hoga1',
    'sell_hoga2',
    'sell_hoga3',
    'sell_hoga4',
    'sell_hoga5',
    'sell_hoga6',
    'sell_hoga7',
    'sell_hoga8',
    'sell_hoga9',
    'sell_hoga10',
    'buy_hoga1',
    'buy_hoga2',
    'buy_hoga3',
    'buy_hoga4',
    'buy_hoga5',
    'buy_hoga6',
    'buy_hoga7',
    'buy_hoga8',
    'buy_hoga9',
    'buy_hoga10',
    'sell_hoga1_stack',
    'sell_hoga2_stack',
    'sell_hoga3_stack',
    'sell_hoga4_stack',
    'sell_hoga5_stack',
    'sell_hoga6_stack',
    'sell_hoga7_stack',
    'sell_hoga8_stack',
    'sell_hoga9_stack',
    'sell_hoga10_stack',
    'buy_hoga1_stack',
    'buy_hoga2_stack',
    'buy_hoga3_stack',
    'buy_hoga4_stack',
    'buy_hoga5_stack',
    'buy_hoga6_stack',
    'buy_hoga7_stack',
    'buy_hoga8_stack',
    'buy_hoga9_stack',
    'buy_hoga10_stack',
    'total_buy_hoga_stack',
    'total_sell_hoga_stack',
    'net_buy_hoga_stack',
    'net_sell_hoga_stack',
    'ratio_buy_hoga_stack',
    'ratio_sell_hoga_stack'
]


class VirtualAPI:

    def __init__(self, api_queue=None):
        """
        Virtual Data API를 사용하면 Google Drive에 저장되어 있는 데이터 소스를 실제 시장 상황처럼 받음으로써
        백테스팅을 할 수 있다. (주의: 실제 시장보다 데이터가 들어오는 속도가 압도적으로 빠를 수도 있다.)
        """
        print('Virtual Data Source Initialized')
        self.api_queue = api_queue

        self.stocks_path = r'G:\공유 드라이브\Project_TBD\Stock_Data\real_time\kiwoom_stocks'
        self.futures_path = r'G:\공유 드라이브\Project_TBD\Stock_Data\real_time\kiwoom_futures'

        self._get_dates()

    def _get_dates(self):
        self.stocks_dates = os.listdir(self.stocks_path)
        self.futures_dates = os.listdir(self.futures_path)

    def stream_data(self, date_from, date_to=None, asset_type='stocks', data_type='trade', time_from='08', time_to='16', monitor_stocks=[]):
        if date_to is None:
            date_to = date_from
        path = self.stocks_path if asset_type == 'stocks' else self.futures_path
        dates = self.stocks_dates if asset_type == 'stocks' else self.futures_dates
        dates = sorted([d for d in dates if (d >= date_from) and (d <= date_to)])
        for date in dates:
            files = os.listdir(f'{path}/{date}')
            files = [f for f in files if f.replace('.csv', '').split('_')[1] == data_type]
            files = sorted([f for f in files
                            if (f.replace('.csv', '').split('_')[-1] >= time_from)
                            and (f.replace('.csv', '').split('_')[-1] <= time_to)])
            for f in files:
                for df in pd.read_csv(f'{path}/{date_from}/{f}',
                                      names=trade_cols if data_type == 'trade' else orderbook_cols,
                                      chunksize=1000000):
                    # chunksize를 설정하지 않으면 32비트 터미널에서 read_csv를 실행할 수 없다.
                    # 300메가 이상되는 파일은 열지 못하는듯
                    df.drop(['rotation', 'strength', 'mkt_type', 'mkt_cap'], axis=1, inplace=True)
                    for i in range(len(df)):
                        data = df.iloc[i, :].to_dict()
                        data['type'] = 'tick'
                        if len(monitor_stocks) > 0:
                            if data['code'] in monitor_stocks:
                                self.api_queue.put(data)
                        else:
                            self.api_queue.put(data)


if __name__ == '__main__':
    v = VirtualAPI(None)
    v.stream_data(date_from='2021-01-29', monitor_stocks=['005930', '000270'])