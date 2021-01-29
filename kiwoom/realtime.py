import datetime
import os, sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import *

from .base import KiwoomBaseAPI
from db import PriceDB

# sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))


class OrderThread(QThread):
    order = pyqtSignal(str)

    def __init__(self, order_queue):
        QThread.__init__(self)
        self.order_queue = order_queue

    def run(self):
        """
        쓰레드에서 order를 받자마자 메인 쓰레드로 보내주기
        """
        while True:
            order_data = self.order_queue.get()
            self.order.emit(order_data)


class KiwoomRealtimeAPI(KiwoomBaseAPI):

    def __init__(self, api_queue, port_queue, order_queue, monitor_stocks, mode='trade', **kwargs):
        """
        mode: trade / api
        
        --> api모드로 설정하면 데이터 수집을 진행할 수 있다.
            분봉 데이터 수집 / 산업 데이터 수집 등
        """
        super().__init__(monitor_stocks)

        self.mode = mode

        self.api_queue = api_queue
        self.port_queue = port_queue
        self.order_queue = order_queue

        print('Initializing Kiwoom API')
        if self.mode == 'trade':
            self.get_account_num()
            self.get_account_info()
            self.get_portfolio_stocks()
            self.get_remaining_orders()
            self.set_monitor_stocks_data()
            self.set_realtime_monitor_stocks()

            self.worker = OrderThread(self.order_queue)
            self.worker.order.connect(self.on_receive_order)
            self.worker.start()

        if self.mode == 'api':
            self.db = PriceDB()
            self.request_minute_data(**kwargs)

    # [API mode function]
    def request_minute_data(self, asset_type='stocks', data_cnt=1):
        """
        :param asset_type: stocks, futures, all
        :param data_cnt: 900개 단위. 즉, 1이면 900
        """
        self.request_break_pt = data_cnt

        if asset_type == 'stocks':
            codelist = self.total_stocks_list
        elif asset_type == 'futures':
            codelist = self.total_futures_list
        else:
            codelist = self.stocks_futures_code

        cnt = 1
        total_cnt = len(codelist)
        for code in codelist:
            print(f'[{cnt}/{total_cnt}] {code}: Request Processing')
            self.get_min_ohlcv(code)
            min_data = self.monitor_stocks_data[code]
            self.db.save_minute_data(code, min_data)
            del self.monitor_stocks_data[code]
            cnt += 1

    # [TRADE mode functions]
    def on_receive_order(self, order):
        print('receive order from main thread')
        print(order)

        # order 주문 넣기

    def set_monitor_stocks_data(self):
        for code in self.monitor_stocks:
            if code != '001':
                self.get_min_ohlcv(code)
            else:
                self.get_sec_ohlcv(code)
            print(f'종목/지수 데이터 수집 완료: {code}')

    def set_realtime_monitor_stocks(self):
        self.set_real_reg('0101', '', self.realType.REALTYPE['장시작시간']['장운영구분'], '0')
        print("실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s" % ('장시작시간', '0101', self.realType.REALTYPE['장시작시간']['장운영구분']))
        try:
            cnt = 0
            screen_no = 1000
            for code in self.monitor_stocks:
                if code != '001': # 코스피 지수 실시간 데이터에서 제외
                    if cnt % 50 == 0:
                        screen_no += 1
                    fid = f"{self.realType.REALTYPE['주식체결']['체결시간']};{self.realType.REALTYPE['주식호가잔량']['매수호가1']}"
                    self.set_real_reg(str(screen_no), code, fid, '1')
                    print("실시간 등록 코드: %s, 스크린번호: %s, fid번호: %s" % (code, screen_no, fid))
                    cnt += 1
        except:
            print('실시간 등록에 실패, 다시 시도')
            self.set_realtime_monitor_stocks()

    def receive_tr_data(self, screen_no, rqname, trcode, record_name, prev_next):
        if prev_next == '2':
            self.data_remains = True
        else:
            self.data_remains = False

        if rqname == "예수금상세현황요청":
            self.opw00001(rqname, trcode)
        elif rqname == '계좌평가잔고내역요청':
            self.opw00018(rqname, trcode, prev_next)
        elif rqname == '실시간미체결요청':
            self.opt10075(rqname, trcode)
        elif rqname == "주식분봉차트조회":
            self.opt10080(rqname, trcode, prev_next)
        elif rqname == '업종일봉차트조회':
            self.opt20006(rqname, trcode, prev_next)

        try:
            if self.data_remains == False:
                self.tr_event_loop.exit()
        except AttributeError:
            pass

    # TR : 예수금상세현황요청
    def opw00001(self, rqname, trcode):
        # 매일 예수금을 변경하고, 투자 금액도 그에 따라 변경한다
        deposit = self.get_comm_data(trcode, rqname, 0, '예수금')
        self.deposit = int(deposit)
        print('예수금: {}'.format(self.deposit))

        available_deposit = self.get_comm_data(trcode, rqname, 0, '출금가능금액')
        available_deposit = int(available_deposit)
        print('출금가능금액: {}'.format(available_deposit))

    # TR : 계좌평가잔고내역요청
    def opw00018(self, rqname, trcode, prev_next):
        total_buy_amount = self.get_comm_data(trcode, rqname, 0, '총매입금액')
        total_buy_amount_result = int(total_buy_amount)
        print("총매입금액 : %s" % total_buy_amount_result)

        total_return = self.get_comm_data(trcode, rqname, 0, '총수익률(%)')
        total_return_result = float(total_return)
        print("총수익률(%%) : %s" % total_return_result)

        rows = self.get_repeat_cnt(trcode, rqname)

        for i in range(rows):
            code = self.get_comm_data(trcode, rqname, i, '종목번호')
            code = code.strip()[1:]

            code_nm = self.get_comm_data(trcode, rqname, i, '종목명')
            stock_quantity = self.get_comm_data(trcode, rqname, i, '보유수량')
            buy_price = self.get_comm_data(trcode, rqname, i, '매입가')
            profit_rate = self.get_comm_data(trcode, rqname, i, '수익률(%)')
            current_price = self.get_comm_data(trcode, rqname, i, '현재가')
            total_buy_amount = self.get_comm_data(trcode, rqname, i, '매입금액')
            possible_quantity = self.get_comm_data(trcode, rqname, i, '매매가능수량')

            if code not in self.portfolio_stocks:
                self.portfolio_stocks.update({code: {}})

            code_nm = code_nm.strip()
            stock_quantity = int(stock_quantity.strip())
            buy_price = int(buy_price.strip())
            profit_rate = float(profit_rate.strip())
            current_price = int(current_price.strip())
            total_buy_amount = int(total_buy_amount.strip())
            possible_quantity = int(possible_quantity.strip())

            self.portfolio_stocks[code].update({'종목명': code_nm})
            self.portfolio_stocks[code].update({'보유수량': stock_quantity})
            self.portfolio_stocks[code].update({'매입가': buy_price})
            self.portfolio_stocks[code].update({'수익률(%)': profit_rate})
            self.portfolio_stocks[code].update({'현재가': current_price})
            self.portfolio_stocks[code].update({'매입금액': total_buy_amount})
            self.portfolio_stocks[code].update({'매매가능수량': possible_quantity})

        if prev_next == '2':
            self.get_portfolio_stocks(prev_next='2')
        else:
            self.tr_event_loop.exit()

    # TR : 실시간미체결요청
    def opt10075(self, rqname, trcode):
        rows = self.get_repeat_cnt(trcode, rqname)

        for i in range(rows):
            code = self.get_comm_data(trcode, rqname, i, '종목코드')
            code_nm = self.get_comm_data(trcode, rqname, i, '종목명')
            order_no = self.get_comm_data(trcode, rqname, i, '주문번호')
            order_status = self.get_comm_data(trcode, rqname, i, '주문상태')
            order_quantity = self.get_comm_data(trcode, rqname, i, '주문수량')
            order_price = self.get_comm_data(trcode, rqname, i, '주문가격')
            order_gubun = self.get_comm_data(trcode, rqname, i, '주문구분')
            not_quantity = self.get_comm_data(trcode, rqname, i, '미체결수량')
            ok_quantity = self.get_comm_data(trcode, rqname, i, '체결량')

            code = code.strip()
            code_nm = code_nm.strip()
            order_no = int(order_no.strip())
            order_status = order_status.strip()
            order_quantity = int(order_quantity.strip())
            order_price = int(order_price.strip())
            order_gubun = order_gubun.strip().lstrip("+").lstrip("-")
            not_quantity = int(not_quantity.strip())
            ok_quantity = int(ok_quantity.strip())

            if order_no not in self.remaining_orders:
                self.remaining_orders.update({order_no: {}})

            self.remaining_orders[order_no].update({"종목코드": code})
            self.remaining_orders[order_no].update({"종목명": code_nm})
            self.remaining_orders[order_no].update({"주문번호": order_no})
            self.remaining_orders[order_no].update({"주문상태": order_status})
            self.remaining_orders[order_no].update({"주문수량": order_quantity})
            self.remaining_orders[order_no].update({"주문가격": order_price})
            self.remaining_orders[order_no].update({"주문구분": order_gubun})
            self.remaining_orders[order_no].update({"미체결수량": not_quantity})
            self.remaining_orders[order_no].update({"체결량": ok_quantity})

            print("미체결 종목 : %s" % self.remaining_orders[order_no])

    #TR : 주식분봉차트요청
    def opt10080(self, rqname, trcode, prev_next):
        code = self.get_comm_data(trcode, rqname, 0, '종목코드')
        code = code.strip()

        data_cnt = self.get_repeat_cnt(trcode, rqname)

        tmp_data = []

        for i in range(data_cnt):
            date = self.get_comm_data(trcode, rqname, i, "체결시간")
            openp = self.get_comm_data(trcode, rqname, i, "시가")
            high = self.get_comm_data(trcode, rqname, i, "고가")
            low = self.get_comm_data(trcode, rqname, i, "저가")
            close = self.get_comm_data(trcode, rqname, i, "현재가")
            volume = self.get_comm_data(trcode, rqname, i, "거래량")

            update_data = {"code": code,
                           "date": int(date),
                           "open": abs(int(openp)),
                           "high": abs(int(high)),
                           "low": abs(int(low)),
                           "close": abs(int(close)),
                           "volume": abs(int(volume))}

            tmp_data.append(update_data)

        if code not in self.monitor_stocks_data.keys():
            self.monitor_stocks_data[code] = tmp_data
        else:
            old_data = self.monitor_stocks_data[code]
            self.monitor_stocks_data[code] = old_data + tmp_data

        self.request_break_cnt += 1

        if (prev_next == '2') and (self.request_break_cnt < self.request_break_pt):
            self.get_min_ohlcv(code, prev_next=prev_next)
        else:
            self.tr_event_loop.exit()

    #TR : 업종일봉조회요청
    def opt20006(self, rqname, trcode, prev_next):
        code = self.get_comm_data(trcode, rqname, 0, '업종코드')
        code = code.strip()

        data_cnt = self.get_repeat_cnt(trcode, rqname)

        tmp_data = []

        for i in range(data_cnt):
            date = self.get_comm_data(trcode, rqname, i, "일자")
            openp = self.get_comm_data(trcode, rqname, i, "시가")
            high = self.get_comm_data(trcode, rqname, i, "고가")
            low = self.get_comm_data(trcode, rqname, i, "저가")
            close = self.get_comm_data(trcode, rqname, i, "현재가")
            volume = self.get_comm_data(trcode, rqname, i, "거래량")

            update_data = {"code": code,
                           "date": int(date),
                           "open": abs(float(openp)),
                           "high": abs(float(high)),
                           "low": abs(float(low)),
                           "close": abs(float(close)),
                           "volume": abs(int(volume))}

            tmp_data.append(update_data)

        if code not in self.monitor_stocks_data.keys():
            self.monitor_stocks_data[code] = tmp_data
        else:
            old_data = self.monitor_stocks_data[code]
            self.monitor_stocks_data[code] = old_data + tmp_data

        self.request_break_cnt += 1

        if (prev_next == '2') and (self.request_break_cnt < self.request_break_pt):
            self.get_sec_ohlcv(code, prev_next=prev_next)
        else:
            self.tr_event_loop.exit()

    def receive_real_data(self, code, real_type, real_data):

        if self.mode == 'api':
            return

        if real_type == "장시작시간":
            fid = self.realType.REALTYPE[real_type]['장운영구분']
            value = self.get_comm_real_data(code, fid)

            if value == "0":
                log_txt = "장 시작 전"
            elif value == "3":
                log_txt = "장 시작!"
            elif value == "2":
                log_txt = "장 종료, 동시호가"
            elif value == "4":
                log_txt = "3시 30분 장 종료!"
            else:
                log_txt = value
            print(log_txt)

        elif (real_type == "주식체결") | (real_type == "선물시세"):
            trade_date = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["체결시간"])
            current_price = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["현재가"])
            open_price = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["시가"])
            high = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["고가"])
            low = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["저가"])
            volume = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["거래량"])
            cum_volume = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["누적거래량"])
            trade_sell_hoga1 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["(최우선)매도호가"])
            trade_buy_hoga1 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["(최우선)매수호가"])

            tick_data = {
                'type': 'tick',
                'code': code.strip(),
                'trade_date': str(trade_date),
                'timestamp': datetime.datetime.now().strftime("%Y%m%d%H%M%S.%f")[:-3],
                'current_price': abs(int(current_price)),
                'open_price': abs(int(open_price)),
                'high': abs(int(high)),
                'low': abs(int(low)),
                'volume': abs(int(volume)),
                'cum_volume': abs(int(cum_volume)),
                'trade_sell_hoga1': abs(int(trade_sell_hoga1)),
                'trade_buy_hoga1': abs(int(trade_buy_hoga1))
            }

            # update_data (data handler로 데이터 보내주기)
            self.api_queue.put(tick_data)

        elif (real_type == "주식호가잔량") | (real_type == "주식선물호가잔량") | (real_type == "선물호가잔량"):
            hoga_date = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["호가시간"])

            processor = int if code in self.total_stocks_list else float

            #### 매도호가
            sell_hoga1 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가1"])
            sell_hoga2 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가2"])
            sell_hoga3 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가3"])
            sell_hoga4 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가4"])
            sell_hoga5 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가5"])

            if (real_type == "주식호가잔량"):
                sell_hoga6 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가6"])
                sell_hoga7 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가7"])
                sell_hoga8 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가8"])
                sell_hoga9 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가9"])
                sell_hoga10 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가10"])
            else:
                sell_hoga6 = None
                sell_hoga7 = None
                sell_hoga8 = None
                sell_hoga9 = None
                sell_hoga10 = None

            ### 매수호가
            buy_hoga1 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가1"])
            buy_hoga2 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가2"])
            buy_hoga3 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가3"])
            buy_hoga4 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가4"])
            buy_hoga5 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가5"])

            if (real_type == "주식호가잔량"):
                buy_hoga6 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가6"])
                buy_hoga7 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가7"])
                buy_hoga8 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가8"])
                buy_hoga9 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가9"])
                buy_hoga10 = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가10"])
            else:
                buy_hoga6 = None
                buy_hoga7 = None
                buy_hoga8 = None
                buy_hoga9 = None
                buy_hoga10 = None

            #### 매도호가수량
            sell_hoga1_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량1"])
            sell_hoga2_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량2"])
            sell_hoga3_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량3"])
            sell_hoga4_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량4"])
            sell_hoga5_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량5"])

            if (real_type == "주식호가잔량"):
                sell_hoga6_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량6"])
                sell_hoga7_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량7"])
                sell_hoga8_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량8"])
                sell_hoga9_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량9"])
                sell_hoga10_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가수량10"])
            else:
                sell_hoga6_stack = None
                sell_hoga7_stack = None
                sell_hoga8_stack = None
                sell_hoga9_stack = None
                sell_hoga10_stack = None

            ### 매수호가수량
            buy_hoga1_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량1"])
            buy_hoga2_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량2"])
            buy_hoga3_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량3"])
            buy_hoga4_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량4"])
            buy_hoga5_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량5"])

            if (real_type == "주식호가잔량"):
                buy_hoga6_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량6"])
                buy_hoga7_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량7"])
                buy_hoga8_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량8"])
                buy_hoga9_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량9"])
                buy_hoga10_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가수량10"])
            else:
                buy_hoga6_stack = None
                buy_hoga7_stack = None
                buy_hoga8_stack = None
                buy_hoga9_stack = None
                buy_hoga10_stack = None

            ##### etc
            if (real_type == "주식호가잔량"):
                total_buy_hoga_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수호가총잔량"])
                total_sell_hoga_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도호가총잔량"])
                net_buy_hoga_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["순매수잔량"])
                net_sell_hoga_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["순매도잔량"])
                ratio_buy_hoga_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매수비율"])
                ratio_sell_hoga_stack = self.get_comm_real_data(code, self.realType.REALTYPE[real_type]["매도비율"])
            else:
                total_buy_hoga_stack = None
                total_sell_hoga_stack = None
                net_buy_hoga_stack = None
                net_sell_hoga_stack = None
                ratio_buy_hoga_stack = None
                ratio_sell_hoga_stack = None

            hoga_data = {
                'type': 'hoga',
                'code': code,
                'hoga_date': abs(processor(hoga_date)),
                'timestamp': datetime.datetime.now().strftime("%Y%m%d%H%M%S.%f")[:-3],
                'sell_hoga1': abs(processor(sell_hoga1)),
                'sell_hoga2': abs(processor(sell_hoga2)),
                'sell_hoga3': abs(processor(sell_hoga3)),
                'sell_hoga4': abs(processor(sell_hoga4)),
                'sell_hoga5': abs(processor(sell_hoga5)),
                'sell_hoga6': abs(processor(sell_hoga6)) if sell_hoga6 is not None else sell_hoga6,
                'sell_hoga7': abs(processor(sell_hoga7)) if sell_hoga7 is not None else sell_hoga7,
                'sell_hoga8': abs(processor(sell_hoga8)) if sell_hoga8 is not None else sell_hoga8,
                'sell_hoga9': abs(processor(sell_hoga9)) if sell_hoga9 is not None else sell_hoga9,
                'sell_hoga10': abs(processor(sell_hoga10)) if sell_hoga10 is not None else sell_hoga10,
                'buy_hoga1': abs(processor(buy_hoga1)),
                'buy_hoga2': abs(processor(buy_hoga2)),
                'buy_hoga3': abs(processor(buy_hoga3)),
                'buy_hoga4': abs(processor(buy_hoga4)),
                'buy_hoga5': abs(processor(buy_hoga5)),
                'buy_hoga6': abs(processor(buy_hoga6)) if buy_hoga6 is not None else buy_hoga6,
                'buy_hoga7': abs(processor(buy_hoga7)) if buy_hoga7 is not None else buy_hoga7,
                'buy_hoga8': abs(processor(buy_hoga8)) if buy_hoga8 is not None else buy_hoga8,
                'buy_hoga9': abs(processor(buy_hoga9)) if buy_hoga9 is not None else buy_hoga9,
                'buy_hoga10': abs(processor(buy_hoga10)) if buy_hoga10 is not None else buy_hoga10,
                'sell_hoga1_stack': abs(processor(sell_hoga1_stack)),
                'sell_hoga2_stack': abs(processor(sell_hoga2_stack)),
                'sell_hoga3_stack': abs(processor(sell_hoga3_stack)),
                'sell_hoga4_stack': abs(processor(sell_hoga4_stack)),
                'sell_hoga5_stack': abs(processor(sell_hoga5_stack)),
                'sell_hoga6_stack': abs(processor(sell_hoga6_stack)) if sell_hoga6_stack is not None else sell_hoga6_stack,
                'sell_hoga7_stack': abs(processor(sell_hoga7_stack)) if sell_hoga7_stack is not None else sell_hoga7_stack,
                'sell_hoga8_stack': abs(processor(sell_hoga8_stack)) if sell_hoga8_stack is not None else sell_hoga8_stack,
                'sell_hoga9_stack': abs(processor(sell_hoga9_stack)) if sell_hoga9_stack is not None else sell_hoga9_stack,
                'sell_hoga10_stack': abs(processor(sell_hoga10_stack)) if sell_hoga10_stack is not None else sell_hoga10_stack,
                'buy_hoga1_stack': abs(processor(buy_hoga1_stack)),
                'buy_hoga2_stack': abs(processor(buy_hoga2_stack)),
                'buy_hoga3_stack': abs(processor(buy_hoga3_stack)),
                'buy_hoga4_stack': abs(processor(buy_hoga4_stack)),
                'buy_hoga5_stack': abs(processor(buy_hoga5_stack)),
                'buy_hoga6_stack': abs(processor(buy_hoga6_stack)) if buy_hoga6_stack is not None else buy_hoga6_stack,
                'buy_hoga7_stack': abs(processor(buy_hoga7_stack)) if buy_hoga7_stack is not None else buy_hoga7_stack,
                'buy_hoga8_stack': abs(processor(buy_hoga8_stack)) if buy_hoga8_stack is not None else buy_hoga8_stack,
                'buy_hoga9_stack': abs(processor(buy_hoga9_stack)) if buy_hoga9_stack is not None else buy_hoga9_stack,
                'buy_hoga10_stack': abs(processor(buy_hoga10_stack)) if buy_hoga10_stack is not None else buy_hoga10_stack,
                'total_buy_hoga_stack': abs(int(total_buy_hoga_stack)),
                'total_sell_hoga_stack': abs(int(total_sell_hoga_stack)),
                'net_buy_hoga_stack': abs(int(net_buy_hoga_stack)),
                'net_sell_hoga_stack': abs(int(net_sell_hoga_stack)),
                'ratio_buy_hoga_stack': abs(float(ratio_buy_hoga_stack)),
                'ratio_sell_hoga_stack': abs(float(ratio_sell_hoga_stack))
            }

            # update_data (data handler로 데이터 보내주기)
            self.api_queue.put(hoga_data)

    def receive_chejan_data(self, gubun, item_cnt, fid_list):

        if int(gubun) == 0:
            # 주문체결
            account_num = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["계좌번호"])
            code = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["종목코드"])[1:]
            stock_name = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["종목명"])
            origin_order_number = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["원주문번호"])
            order_number = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["주문번호"])
            order_status = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["주문상태"])
            order_quan = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["주문수량"])
            order_price = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["주문가격"])
            not_chegual_quan = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["미체결수량"])
            order_gubun = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["주문구분"])
            chegual_time_str = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["주문/체결시간"])
            chegual_price = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["체결가"])
            chegual_quantity = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["체결량"])
            current_price = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["현재가"])
            first_sell_price = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["(최우선)매도호가"])
            first_buy_price = self.get_chegan_data(self.realType.REALTYPE["주문체결"]["(최우선)매수호가"])

            che_data = {
                'type': 'che',
                'account_num': account_num,
                'code': code,
                'stock_name': stock_name.strip(),
                'origin_order_number': origin_order_number,
                'order_number': order_number,
                'order_status': order_status,
                'order_quan': int(order_quan),
                'order_price': int(order_price),
                'not_chegual_quan': int(not_chegual_quan),
                'order_gubun': order_gubun.strip().lstrip("+").lstrip("-"),
                'chegual_time_str': chegual_time_str,
                'chegual_price': int(chegual_price) if chegual_price != '' else 0,
                'chegual_quantity': int(chegual_quantity) if chegual_quantity != '' else 0,
                'current_price': abs(int(current_price)),
                'first_sell_price': abs(int(first_sell_price)),
                'first_buy_price': abs(int(first_buy_price))
            }

            # update_data (portfolio로 데이터 보내주기)
            # 이벤트로 수정해주기
            self.port_queue.put(che_data)

        elif int(gubun) == 1:
            # 잔고
            account_num = self.get_chegan_data(self.realType.REALTYPE['잔고']['계좌번호'])
            code = self.get_chegan_data(self.realType.REALTYPE['잔고']['종목코드'])[1:]
            stock_name = self.get_chegan_data(self.realType.REALTYPE['잔고']['종목명'])
            current_price = self.get_chegan_data(self.realType.REALTYPE['잔고']['현재가'])
            stock_quan = self.get_chegan_data(self.realType.REALTYPE['잔고']['보유수량'])
            avail_quan = self.get_chegan_data(self.realType.REALTYPE['잔고']['주문가능수량'])
            buy_price = self.get_chegan_data(self.realType.REALTYPE['잔고']['매입단가'])
            total_buy_price = self.get_chegan_data(self.realType.REALTYPE['잔고']['총매입가'])
            meme_gubun = self.get_chegan_data(self.realType.REALTYPE['잔고']['매도매수구분'])
            first_sell_price = self.get_chegan_data(self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_buy_price = self.get_chegan_data(self.realType.REALTYPE['잔고']['(최우선)매수호가'])

            jan_data = {
                'type': 'jan',
                'account_num': account_num,
                'code': code,
                'stock_name': stock_name.strip(),
                'current_price': abs(int(current_price)),
                'stock_quan': int(stock_quan),
                'avail_quan': int(avail_quan),
                'buy_price': abs(int(buy_price)),
                'total_buy_price': int(total_buy_price),
                'meme_gubun': self.realType.REALTYPE["매도수구분"][meme_gubun],
                'first_sell_price': abs(int(first_sell_price)),
                'first_buy_price': abs(int(first_buy_price))
            }

            # update_data (portfolio로 데이터 보내주기)
            # 이벤트로 수정해주기
            self.port_queue.put(jan_data)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = KiwoomRealtimeAPI()
    sys.exit(app.exec_())