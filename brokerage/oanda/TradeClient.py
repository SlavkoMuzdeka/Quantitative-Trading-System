import json
import pandas as pd

import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.instruments as instruments


class TradeClient:
    def __init__(self, auth_config):
        self.id = auth_config["oan_acc_id"]
        self.token = auth_config["oan_token"]
        self.env = auth_config["oan_env"]
        self.client = oandapyV20.API(access_token=self.token, environment=self.env)

    def get_account_details(self):
        try:
            return self.client.request(accounts.AccountDetails(accountID=self.id))[
                "account"
            ]
        except Exception as err:
            pass

    def get_account_instruments(self):
        try:
            r = self.client.request(accounts.AccountInstruments(accountID=self.id))[
                "instruments"
            ]
            instruments = {}
            currencies, cfds, metals = (
                [],
                [],
                [],
            )  # fx, index cds + commodities + bonds, metals
            for inst in r:
                inst_name = inst["name"]
                type = inst["type"]
                instruments[inst_name] = {
                    "type": type,
                    # other things
                }
                if type == "CFD":
                    cfds.append(inst_name)
                elif type == "CURRENCY":
                    currencies.append(inst_name)
                elif type == "METAL":
                    metals.append(inst_name)
        except Exception as err:
            print(err)

    def get_account_summary(self):
        try:
            return self.client.request(accounts.AccountSummary(accountID=self.id))
        except Exception as err:
            raise Exception("Some err message from acc summary: {}".format(str(err)))

    def get_account_capital(self):
        try:
            return float(self.get_account_summary()["NAV"])
        except Exception as err:
            pass

    def get_account_position(self):
        positions_data = self.get_account_details()["positions"]
        positions = {}
        for entry in positions_data:
            instrument = entry["instrument"]
            long_pos = int(entry["long"]["units"])
            short_pos = int(entry["long"]["units"])
            net_pos = long_pos + short_pos
            if net_pos != 0:
                positions[instrument] = net_pos
        return positions

    def get_account_trades(self):
        try:
            trades = self.client.request(trades.OpenTrades(accountID=self.id))

        except Exception as err:
            pass

    def is_tradable(self, inst):
        try:
            params = {"instruments": inst}
            r = pricing.PricingInfo(accountID=self.id, params=params)
            res = self.client.request(r)
            is_tradable = res["prices"][0]["tradeable"]
            return is_tradable
        except Exception as err:
            print(err)

    def get_account_orders(self):
        pass

    def get_endpoint(self, inst):
        pass

    def get_ohlcv(self, instrument, const, granularity):
        pass

    def market_order(self, inst, order_config={}):
        pass
