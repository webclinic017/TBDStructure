from prac import Port
from prac import Bar
from multiprocessing  import Process



if __name__ == '__main__':
    bar = Bar()
    bar.data2 = "goodbye"
    port = Port()

    p1 = Process(target=port.say_hello)
    p2 = Process(target=port.say_bye)

    p1.start()
    p2.start()