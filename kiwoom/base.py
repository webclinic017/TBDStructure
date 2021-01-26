import datetime, requests, sys, os

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMainWindow

from errcode import *
from realtype import *
from const import *

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

SLEEP_TIME = 3.8


class KiwoomBaseAPI(QMainWindow):
    '''
    Base API 클래스는 로그인/관심종목 등록까지 처리
    '''

    def __init__(self):
        super().__init__()

        self.kiwoom = self.create_kiwoom_ocx_instance()
        self.set_events_callback()
        self.set_real_time_events_callback()
        self.login_comm_connect()

        self.realType = RealType()
        self.account_num = None             # 계좌번호
        self.deposit = None                 # 예수금
        self.round_bet_amount = None        # 1차 투자/배팅 금액
        self.portfolio_stocks = {}          # 계좌평가잔고내역 (보유 종목 정보) --> 데이터 세팅하면서 제거됨
        self.monitor_portfolio_stocks = {}  # 관심종목 계좌평가잔고내역
        self.remaining_orders = {}          # 실시간미체결정보
        self.min_data = {}                  # Temporary Data: 분봉 데이터 모아두는 곳 --> 제거됨
        self.sec_data = {}                  # Temporary Data: 업종 데이터 --> 제거됨
        self.request_break_cnt = 0          # 데이터 세팅 중 요청 횟수 카운팅 변수
        self.request_break_pt = 1           # 데이터 세팅 중 최대 요청 횟수
        self.stop_order_switch = 0          # 주문이 들어간 상태에서 모든 주문을 막는 스위치
        self.stop_realtime_switch = 1       # 실시간 데이터가 등록되기 전에 실시간 스트림을 막는 스위치

        self.user_state = True
        self.market_state = 1
        self.port_state = ''

        self.today_date = datetime.datetime.now().strftime('%Y%m%d')
        self.monitor_stocks_list = []
        self.monitor_stocks_data = {}

        # 전처리 작업: 관심종목 불러오기
        self.get_monitor_stocks_list()

    def get_monitor_stocks_list(self):
        codelist = GET_MONITORSTOCKS()
        self.monitor_stocks_list = [code.strip() for code in codelist] + ['001']

    def create_kiwoom_ocx_instance(self):
        return QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')

    def set_events_callback(self):
        self.kiwoom.OnEventConnect.connect(self.login_callback)
        self.kiwoom.OnReceiveTrData.connect(self.receive_tr_data)

    def set_real_time_events_callback(self):
        self.kiwoom.OnReceiveRealData.connect(self.receive_real_data)
        self.kiwoom.OnReceiveChejanData.connect(self.receive_chejan_data)

    def receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next):
        pass

    def receive_real_data(self, code, real_type, real_data):
        pass

    def receive_chejan_data(self, gubun, item_cnt, fid_list):
        pass

    def login_callback(self, errcode):
        print('로그인 처리 코드: {}'.format(errors(errcode)))
        self.login_event_loop.exit()

    def login_comm_connect(self):
        self.kiwoom.dynamicCall('CommConnect()')
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_login_info(self):
        account_num = self.kiwoom.dynamicCall('GetLoginInfo(QString)', 'ACCNO')
        return account_num

    def set_input_value(self, id, value):
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, prev_next, screen_no):
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, prev_next, screen_no)
        if prev_next == '0':
            self.request_break_cnt = 0
            self.tr_event_loop = QEventLoop()
            self.tr_event_loop.exec_()

    def get_comm_data(self, trcode, rqname, index, item_name):
        ret = self.kiwoom.dynamicCall('GetCommData(QString, QString, int, QString)', trcode, rqname, index, item_name)
        return ret

    def get_repeat_cnt(self, trcode, rqname):
        cnt = self.kiwoom.dynamicCall("GetRepeatCnt(Qstring, Qstring)", trcode, rqname)
        return cnt

    def set_real_reg(self, screen_no, code, fid, set_no):
        params = [screen_no, code, fid, set_no]
        self.kiwoom.dynamicCall("SetRealReg(QString, QString, QString, QString)", params)

    def get_comm_real_data(self, code, fid):
        ret = self.kiwoom.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return ret

    def get_chegan_data(self, fid):
        ret = self.kiwoom.dynamicCall("GetChejanData(int)", fid)
        return ret

    def set_real_remove(self, screen_no, code):
        self.kiwoom.dynamicCall("SetRealRemove(QString, QString)", screen_no, code)

    def send_order(self, rqname, screen_no, acc_no, order_type, code, qty, price, hoga_gb, org_order_no=''):
        params = [
            rqname,
            screen_no,
            acc_no,
            order_type,
            code,
            qty,
            price,
            hoga_gb,
            org_order_no
        ]
        order_res = self.kiwoom.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            params
        )
        return order_res

    def get_account_num(self):
        account_list = self.get_login_info()
        self.account_num = account_list.split(';')[0]
        print('계좌번호: {}'.format(self.account_num))

    def get_account_info(self):
        self.set_input_value('계좌번호', self.account_num)
        self.set_input_value('비밀번호', '0000')
        self.set_input_value('비밀번호입력매체구분', '00')
        self.set_input_value('조회구분', '2')
        self.comm_rq_data('예수금상세현황요청', 'opw00001', '0', '2000')

    def get_portfolio_stocks(self, prev_next='0'):
        self.set_input_value('계좌번호', self.account_num)
        self.set_input_value('비밀번호', '0000')
        self.set_input_value('비밀번호입력매체구분', '00')
        self.set_input_value('조회구분', '2')
        self.comm_rq_data('계좌평가잔고내역요청', 'opw00018', prev_next, '2001')

    def get_remaining_orders(self):
        self.set_input_value('계좌번호', self.account_num)
        self.set_input_value('체결구분', '1')
        self.set_input_value('매매구분', '0')
        self.comm_rq_data('실시간미체결요청', 'opt10075', '0', '2002')

    def get_min_ohlcv(self, code, prev_next='0'):
        QTest.qWait(SLEEP_TIME)
        self.set_input_value("종목코드", code)
        self.set_input_value("틱범위", "15")
        self.set_input_value("수정주가구분", "0")
        self.comm_rq_data("주식분봉차트조회", "opt10080", prev_next, '2003')

    def get_sec_ohlcv(self, code, prev_next='0'):
        QTest.qWait(SLEEP_TIME)
        self.set_input_value("업종코드", code)
        self.comm_rq_data("업종일봉차트조회", "opt20006", prev_next, '2004')

    def exit_program(self):
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = KiwoomBaseAPI()
    sys.exit(app.exec_())