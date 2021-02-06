from strategies.strategy_1 import Strategy_1
from strategies.strategy_2 import Strategy_2

"""
STRATEGY constant를 생성하여 runner에서 전략명으로 클래스를 호출할 수 있도록하기
"""
STRATEGY = {
    'strategy_1': Strategy_1,
    'strategy_2': Strategy_2
}