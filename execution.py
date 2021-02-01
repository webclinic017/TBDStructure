from event import FillEvent
import datetime
import win32com.client
import pythoncom
import pandas as pd
import threading
from ebest import ebest_execution


class ExecutionHandler:
    def __init__(self, port_queue, order_queue, server="demo", source='backtest'):
        """
        source: backtest, kiwoom, ebest, binance etc.
        """
        print('Execution Handler started')
        self.port_queue = port_queue
        self.order_queue = order_queue
        self.source = source

        if self.source == "ebest":
            ebest_execution.EbestExec(self.port_queue, server=server) # FillEvent는 XR_event_handler 참조, port_queue로 Fill 보냄

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

                ebest_execution.Ebest.CSPAT00600_request(order_type=event.order_type,
                                                         AcntNo=ebest_execution.Ebest.acc_no_stock,
                                                         InptPwd=ebest_execution.Ebest.acc_pw,
                                                         IsuNo=event.symbol,
                                                         OrdQty=event.quantity, BnsTpCode=direction)

        if self.source == 'binance':
            pass

    def start_execution_loop(self):
        while True:
            event = self.order_queue.get()
            if event.type == 'ORDER':
                self.execute_order(event)
            else:
                print(f'Wrong Event type: {event.type}')


