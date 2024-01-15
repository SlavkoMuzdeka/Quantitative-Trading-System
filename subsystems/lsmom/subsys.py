"""
[(32, 155), (218, 234), (29, 53), (51, 81), (204, 248), (76, 129), (48, 195), (99, 104), 
(94, 158), (56, 205), (103, 217), (21, 150), (117, 217), (270, 283), (154, 283), (129, 282), (29, 224), (31, 143), (103, 218), (153, 269), (42, 146)]
"""


class Lsmom:
    def __init__(self):
        self.pairs = [
            (32, 155),
            (218, 234),
            (29, 53),
            (51, 81),
            (204, 248),
            (76, 129),
            (48, 195),
            (99, 104),
            (94, 158),
            (56, 205),
            (103, 217),
            (21, 150),
            (117, 217),
            (270, 283),
            (154, 283),
            (129, 282),
            (29, 224),
            (31, 143),
            (103, 218),
            (153, 269),
            (42, 146),
        ]

    # A function to get extra indicators specific to this strategy
    # A function to run a backtest/get positions from this strategy

    def extend_historical(self, instruments, historical_data):
        pass

    def run_simulation(self, historical_data):
        pass

    def get_subsys_pos(self):
        pass
