from execution import ExecutionHandler


class Portfolio:
    def __init__(self, port_queue):
        print('Portfolio started')
        self.port_queue = port_queue

        self.execution_handler = ExecutionHandler(port_queue=port_queue)

    def update_timeindex(self, event):
        pass

    def update_signal(self, event):
        pass

    def update_fill(self, event):
        pass

    def start_event_loop(self):
        """
        Portfolio 클래스의 이벤트 루프를 실행하여,
        DataHandler의 MarketEvent, Strategy의 OrderEvent, Execution의 FillEvent를 기다린다.
        Event가 도달하면 바로 처리하는 방식으로 작동한다.
        """
        while True:
            event = self.port_queue.get()

            if event.type == 'MARKET':
                self.update_timeindex(event)

            if event.type == 'SIGNAL':
                self.update_signal(event)

            if event.type == 'ORDER':
                self.execution_handler.execute_order(event)

            if event.type == 'FILL':
                self.update_fill(event)