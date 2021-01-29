import sys
from PyQt5.QtWidgets import QApplication

from kiwoom.realtime import KiwoomRealtimeAPI


def get_minute_data_from_kiwoom(asset_type='stocks', data_cnt=1):
    app = QApplication(sys.argv)
    kwargs = {
        'asset_type': asset_type,
        'data_cnt': data_cnt
    }
    _ = KiwoomRealtimeAPI(None, None, None, [], mode='api', **kwargs)
    sys.exit(app.exec_())


if __name__ == '__main__':
    get_minute_data_from_kiwoom(data_cnt=2)