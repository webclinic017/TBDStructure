import pandas as pd
from db import UserDB, PriceDB

try:
    from ebest import ebest_execution
except:
    print('Ebest와 관련된 Execution 모듈을 제대로 install 해주기 바랍니다.')


class ExecutionHandler:
    def __init__(self, port_queue, order_queue, server="demo", source='virtual', strategy_acc_no={}):
        """
        source: backtest, kiwoom, ebest, binance etc.
        """
        print('Execution Handler started')
        self.port_queue = port_queue
        self.order_queue = order_queue

        self.source = source

        self.strategy_acc_no = strategy_acc_no # {strategy_name: [account_num1, account_num2]} for 잔고 업데이트

        if self.source == "ebest":
            if server == "demo":
                server = server
            elif server == "real":
                server = "hts"

            self.credentials = pd.read_csv("./credentials/credentials.csv", index_col=0, dtype=str).loc[server, :]
            ebest_execution.EbestExec(self.order_queue,
                                      server=server, strategy_acc_no=self.strategy_acc_no)  # FillEvent는 XR_event_handler 참조, port_queue로 Fill 보냄

    def execute_order(self, event):
        if self.source == 'virtual':
            # OrderEvent로 바로 FillEvent생성하기
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

                # 주식 코드 6자리, 추후 더 정교하게 수정?
                if len(event.symbol) == 6:
                    ebest_execution.Ebest.CSPAT00600_request(order_type=event.order_type,
                                                             AcntNo=ebest_execution.Ebest.acc_no_stock,
                                                             InptPwd=ebest_execution.Ebest.acc_pw,
                                                             IsuNo=event.symbol,
                                                             OrdQty=event.quantity, BnsTpCode=direction)
                # 주식선물 코드 8자리, 추후 더 정교하게 수정?
                elif len(event.symbol) == 8:
                    ebest_execution.Ebest.CFOAT00100_request(order_type=event.order_type,
                                                             AcntNo=ebest_execution.Ebest.acc_no_future,
                                                             Pwd=ebest_execution.Ebest.acc_pw,
                                                             FnoIsuNo=event.symbol,
                                                             OrdQty=event.quantity, BnsTpCode=direction)

        if self.source == 'binance':
            pass

    # 나중에 Accno를 확인해 전략별로 다른 port_queue를 통해 FillEvent 뿌려주기 (Portfolio를 여러개 생성 할 경우)
    def filter_fill_event(self, event):
        if event.accno == self.credentials["acc_no_stocks"]:
            fill_event = event  # , event.est_fill_cost) 슬리피지 계산위해 고려해보기?
            print(fill_event)
            self.port_queue.put(fill_event)

        elif event.accno == self.credentials["acc_no_futures"]:
            fill_event = event  # , event.est_fill_cost) 슬리피지 계산위해 고려해보기?
            print(fill_event)
            self.port_queue.put(fill_event)

    def start_execution_loop(self):
        while True:
            event = self.order_queue.get()

            if event.type == 'ORDER':
                self.execute_order(event)
            elif event.type == 'FILL':
                self.filter_fill_event(event)
            elif event.type == 'JANGO':
                self.port_queue.put(event)
            else:
                print(f'Wrong Event type: {event.type}')
