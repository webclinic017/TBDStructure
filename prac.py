from multiprocessing import Process

class Bar:
    def __init__(self):
        self.data1 = 'hello'
        self.data2 = 'bye'

class Port(Bar):
    def __init__(self):
        super().__init__()
        self.a = 1
        self.data2 = "goodbyrrr"

    def say_hello(self):
        print(self.data1)

    def say_bye(self):
        print(self.data2)


