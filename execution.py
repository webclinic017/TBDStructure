from event import FillEvent
import datetime
import win32com.client
import pythoncom
import pandas as pd
import threading

class ExecutionHandler:
    def __init__(self, port_queue, source='backtest'):
        """
        source: backtest, kiwoom, ebest, binance etc.
        """
        print('Execution Handler started')
        self.port_queue = port_queue
        self.source = source

        if self.source == "ebest":
            EbestExec(self.port_queue, server="demo") # FillEvent는 XR_event_handler 참조

    def execute_order(self, event):
        if self.source == 'backtest':
            pass

        if self.source == 'kiwoom':
            pass

        if self.source == 'ebest':
            if event.type == "ORDER":
                direction = None
                if event.direction == "BUY":
                    direction = "2"
                elif event.direction == "SELL":
                    direction = "1"
                else:
                    print("put right direction: BUY or SELL")

                Ebest.CSPAT00600_request(event.order_type, AcntNo=Ebest.acc_no_stock, InptPwd=Ebest.acc_pw,
                                             IsuNo=event.symbol,
                                             OrdQty=event.quantity, BnsTpCode=direction)

        if self.source == 'binance':
            pass
        
# Ebest: Object
class Ebest:
    server = "demo"  # hts:실투자, demo: 모의투자
    credentials = pd.read_csv("./credentials/credentials.csv", index_col=0, dtype=str).loc[server, :]

    login_ok = False  # Login
    tr_ok = False  # TR요청
    real_ok = False  # 실시간 요청
    acc_no_stock = credentials["acc_no_stocks"]  # 주식 계좌번호
    acc_no_future = credentials["acc_no_futures"]  # 주식선물 계좌번호
    acc_pw = credentials["acc_pw"]  # 계좌비밀번호

    acc_balance = {}

    tr_event = None  # TR요청에 대한 API 정보
    CSPAT00600_event = None
    SC0_event = None  # 주문접수에 대한 데이터
    SC1_event = None  # 주문체결에 대한 데이터

    t0424_request = None # TR: 잔고 함수
    CSPAT00600_request = None # TR: 주문 함수
    events = None

# Ebest: Real
class XR_event_handler:
    def OnReceiveRealData(self, code):

        if code == "SC0":
            ordno = self.GetFieldData("OutBlock", "ordno")  # 주문번호
            shtcode = self.GetFieldData("OutBlock", "shtcode")  # 종목코드 7자리
            ordtm = self.GetFieldData("OutBlock", "ordtm")  # 주문시간
            ordqty = self.GetFieldData("OutBlock", "ordqty")  # 주문수량
            ordgb = self.GetFieldData("OutBlock", "ordgb") # 주문구분(01: 현금매도, 02: 현금매수, 03: 신용매도, 04: 신용매수)
            # ordamt = self.GetFieldData("OutBlock", "ordamt")  # 주문금액
            # ordablemny = self.GetFieldData("OutBlock", "ordablemny")  # 주문가능현금
            print("주문접수 SC0, 주문시간: %s, 주문번호: %s, 주문수량: %s, 주문구분: %s, 종목코드: %s" % (ordtm, ordno, ordqty, ordgb, shtcode), flush=True)

        elif code == "SC1":
            ordno = self.GetFieldData("OutBlock", "ordno")  # 주문번호
            execqty = self.GetFieldData("OutBlock", "execqty")  # 체결수량
            execprc = self.GetFieldData("OutBlock", "execprc")  # 체결가격
            shtnIsuno = self.GetFieldData("OutBlock", "shtnIsuno")  # 종목코드 7자리 ??? 잇나?
            Isuno = self.GetFieldData("OutBlock", "Isuno") # 종목번호 형태모름...
            exectime = self.GetFieldData("OutBlock", "exectime")  # 체결시간
            mnyexecamt = self.GetFieldData("OutBlock", "mnyexecamt")  # 현금체결금액 (신용체결금액도 있음) # 나중에 써보기
            bnstp = self.GetFieldData("OutBlock", "bnstp") # 매매구분 (1:매도 , 2: 매수) , 주문구분이 체결에는 없는듯..?
            print("주문체결 SC1, 체결시간: %s, 주문번호: %s, 체결수량: %s, 체결가격: %s, 종목코드: %s" % (exectime, ordno, execqty, execprc, shtnIsuno), flush=True)

            shtnIsuno = shtnIsuno[1:]
            fill_cost = int(execqty) * int(execprc)
            direction = None
            if bnstp == "1":
                direction = "SELL"
            elif bnstp == "2":
                direction = "BUY"

            fill_event = FillEvent(datetime.datetime.utcnow(),
                                   shtnIsuno,
                                   'ebest',
                                   int(execqty), direction, fill_cost, None) #, event.est_fill_cost) 슬리피지 계산위해 고려해보기?
            Ebest.events.put(fill_event)

# Ebest: TR
class XQ_event_handler:

    def OnReceiveData(self, code):
        print("%s 수신" % code, flush=True)

        # TR: 잔고 조회
        if code == "t0424":
            cts_expcode = self.GetFieldData("t0424OutBlock", "cts_expcode", 0)
            occurs_count = self.GetBlockCount("t0424OutBlock1")

            for i in range(occurs_count):
                expcode = self.GetFieldData("t0424OutBlock1", "expcode", i)

                if expcode not in Ebest.acc_balance.keys():
                    Ebest.acc_balance[expcode] = {}

                tt = Ebest.acc_balance[expcode]
                tt["잔고수량"] = int(self.GetFieldData("t0424OutBlock1", "janqty", i))
                tt["매도가능수량"] = int(self.GetFieldData("t0424OutBlock1", "mdposqt", i))
                tt["평균단가"] = int(self.GetFieldData("t0424OutBlock1", "pamt", i))
                tt["종목명"] = self.GetFieldData("t0424OutBlock1", "hname", i)
                tt["종목구분"] = self.GetFieldData("t0424OutBlock1", "jonggb", i)
                tt["수익률"] = float(self.GetFieldData("t0424OutBlock1", "sunikrt", i))

            print("잔고내역 %s" % Ebest.acc_balance, flush=True)

            if self.IsNext is True: # 과거 데이터가 더 존재한다.
                Ebest.t0424_request(cts_expcode=cts_expcode, next=self.IsNext)
            elif self.IsNext is False:
                print("Total 잔고내역 %s" % Ebest.acc_balance, flush=True)
                # 잔고 많이 만들어서 확인해보기?!
                Ebest.tr_ok = True


    def OnReceiveMessage(self, systemError, messageCode, message):
        print("systemError: %s, messageCode: %s, message: %s" % (systemError, messageCode, message), flush=True)

# Ebest: Login
class XS_event_handler:

    def OnLogin(self, szCode, szMsg):
        print("%s %s" % (szCode, szMsg), flush=True)
        if szCode == "0000":
            Ebest.login_ok = True
        else:
            Ebest.login_ok = False

# Ebest: Exec
class EbestExec:
    def __init__(self, events, server="demo"):
        print("Ebest Exec")
        Ebest.events = events
        Ebest.server = server

        #로그인
        session = win32com.client.DispatchWithEvents("XA_Session.XASession", XS_event_handler)
        session.ConnectServer(Ebest.server + ".ebestsec.co.kr", 20001)  # 서버 연결
        session.Login(Ebest.credentials["ID"], Ebest.credentials["PW"], Ebest.credentials["gonin_PW"], 0,
                      False)  # 서버 연결

        while Ebest.login_ok is False:
            pythoncom.PumpWaitingMessages()

        # 잔고: TR
        Ebest.tr_event = win32com.client.DispatchWithEvents("XA_DataSet.XAQuery", XQ_event_handler)
        Ebest.tr_event.ResFileName = "C:/eBEST/xingAPI/Res/t0424.res"
        Ebest.t0424_request = self.t0424_request
        Ebest.acc_balance = {}
        Ebest.t0424_request(cts_expcode="", next=False)

        # 주식 주문: TR
        Ebest.CSPAT00600_event = win32com.client.DispatchWithEvents("XA_DataSet.XAQuery", XQ_event_handler)
        Ebest.CSPAT00600_event = win32com.client.DispatchWithEvents("XA_DataSet.XAQuery", XQ_event_handler)
        Ebest.CSPAT00600_event.ResFileName = "C:/eBEST/xingAPI/Res/CSPAT00600.res"
        Ebest.CSPAT00600_request = self.CSPAT00600_request

        threading.Thread(target=self.start_real_events).start()

    def start_real_events(self):
        pythoncom.CoInitialize()

        # 주식 주문접수: Real
        Ebest.SC0_event = win32com.client.DispatchWithEvents("XA_DataSet.XAReal", XR_event_handler)
        Ebest.SC0_event.ResFileName = "C:/eBEST/xingAPI/Res/SC0.res"
        Ebest.SC0_event.AdviseRealData()

        # 주식 체결: Real
        Ebest.SC1_event = win32com.client.DispatchWithEvents("XA_DataSet.XAReal", XR_event_handler)
        Ebest.SC1_event.ResFileName = "C:/eBEST/xingAPI/Res/SC1.res"
        Ebest.SC1_event.AdviseRealData()

        while Ebest.real_ok is False:
            pythoncom.PumpWaitingMessages()

        pythoncom.CoUninitialize()
        # threading.Thread(target=self.start_real_events).join()

    def t0424_request(self, cts_expcode=None, next=None):
        # TR: 주식선물 종목코드 가져오기
        Ebest.tr_event = win32com.client.DispatchWithEvents("XA_DataSet.XAQuery", XQ_event_handler)

        Ebest.tr_event.ResFileName = "C:/eBEST/xingAPI/Res/t0424.res"
        Ebest.tr_event.SetFieldData("t0424InBlock", "accno", 0, Ebest.acc_no_stock)
        Ebest.tr_event.SetFieldData("t0424InBlock", "passwd", 0, Ebest.acc_pw)
        Ebest.tr_event.SetFieldData("t0424InBlock", "prcgb", 0, "1")
        Ebest.tr_event.SetFieldData("t0424InBlock", "chegb", 0, "2")
        Ebest.tr_event.SetFieldData("t0424InBlock", "dangb", 0, "0")
        Ebest.tr_event.SetFieldData("t0424InBlock", "charge", 0, "0")  # 제비용 포함여부 0: 미포함, 1: 포함
        Ebest.tr_event.SetFieldData("t0424InBlock", "cts_expcode", 0, "")

        Ebest.tr_event.Request(next)

        Ebest.tr_ok = False
        while Ebest.tr_ok is False:
            pythoncom.PumpWaitingMessages()

    def CSPAT00600_request(self, order_type, AcntNo=None, InptPwd=None, IsuNo=None, OrdQty=0, BnsTpCode=None):
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "AcntNo", 0, AcntNo)  # 계좌번호
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "InptPwd", 0, InptPwd)  # 비밀번호

        if Ebest.server == "demo":
            IsuNo = "A" + IsuNo

        ot = None
        if order_type == "MKT":
            ot = "03"
        elif order_type == "LMT":
            ot = "00"
        else:
            print("put correct order type! MKT or LMT")

        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "IsuNo", 0, IsuNo)  # 종목번호
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "OrdQty", 0, OrdQty)  # 주문수량
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "OrdPrc", 0, 0)  # 주문가
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "BnsTpCode", 0, BnsTpCode)  # 1:매도, 2:매수
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "OrdprcPtnCode", 0, ot)  # 호가유형코드, 03:시장가
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "MgntrnCode", 0, "000")  # 신용거래코드, 000:보통
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "LoanDt", 0, "")  # 대출일
        Ebest.CSPAT00600_event.SetFieldData("CSPAT00600InBlock1", "OrdCndiTpCode", 0,
                                                "0")  # 주문조건구분 0:없음, 1:IOC, 2:FOK

        err = Ebest.CSPAT00600_event.Request(False)
        if err < 0:
            print("\nXXXXXXXXXXXXXXX "
                  "\nCSPAT00600 주문에러"
                  "\n계좌번호: %s"
                  "\n종목코드: %s"
                  "\n주문수량: %s"
                  "\n매매구분: %s"
                  "\n주문에러: %s"
                  "\n\n" % (AcntNo, IsuNo, OrdQty, BnsTpCode, err), flush=True)

        else:
            print("\n============="
                  "\nCSPAT00600 주문 실행"
                  "\n계좌번호: %s"
                  "\n종목코드: %s"
                  "\n주문수량: %s"
                  "\n매매구분: %s"
                  "\n주문에러: %s"
                  "\n\n" % (AcntNo, IsuNo, OrdQty, BnsTpCode, err), flush=True)