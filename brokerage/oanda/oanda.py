from brokerage.oanda.TradeClient import TradeClient


class Oanda:
    def __init__(self, auth_config=""):
        self.trade_client = TradeClient(auth_config=auth_config)

    def get_trade_client(self):
        return self.trade_client

    # lets craete two different classes for Oanda
