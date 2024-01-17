import json
import pandas as pd
import datetime

import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.instruments as instruments


class TradeClient:
    """
    The class TradeClient provides code with methods to interact
    with an OANDA trading account, retreive account infromation,
    check tradability of instruments, fetch OHLCV data and perform
    other trading-related operations
    """

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
            raise Exception(
                "Some err message from account details: {}".format(str(err))
            )

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
            return instruments, currencies, cfds, metals
        except Exception as err:
            raise Exception(
                "Some err message from account instruments: {}".format(str(err))
            )

    def get_account_summary(self):
        try:
            return self.client.request(accounts.AccountSummary(accountID=self.id))[
                "account"
            ]
        except Exception as err:
            raise Exception(
                "Some err message from account summary: {}".format(str(err))
            )

    def get_account_capital(self):
        try:
            return float(self.get_account_summary()["NAV"])
        except Exception as err:
            raise Exception(
                "Some err message from account capital: {}".format(str(err))
            )

    def get_account_positions(self):
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
            results = self.client.request(trades.OpenTrades(accountID=self.id))
            return results
        except Exception as err:
            raise Exception("Some err message from account trades: {}".format(str(err)))

    def is_tradable(self, inst):
        try:
            params = {"instruments": inst}
            r = pricing.PricingInfo(accountID=self.id, params=params)
            res = self.client.request(r)
            is_tradable = res["prices"][0]["tradeable"]
            return is_tradable
        except Exception as err:
            raise Exception("Some err message from is tradable: {}".format(str(err)))

    def get_account_orders(self):
        pass

    def get_endpoint(self, inst):
        pass

    def format_date(self, series):
        yymmdd = series.split("T")[0].split("-")
        return datetime.date(int(yymmdd[0]), int(yymmdd[1]), int(yymmdd[2]))

    def get_ohlcv(self, instrument, count, granularity):
        try:
            params = {"count": count, "granularity": granularity}
            candles = instruments.InstrumentsCandles(
                instrument=instrument, params=params
            )
            self.client.request(candles)
            ohlc_dict = candles.response["candles"]
            ohlc = pd.DataFrame(ohlc_dict)
            ohlc = ohlc[ohlc["complete"]]
            ohlc_df = ohlc["mid"].dropna().apply(pd.Series)
            ohlc_df["volume"] = ohlc["volume"]
            ohlc_df.index = ohlc["time"]
            ohlc_df = ohlc_df.apply(pd.to_numeric)
            ohlc_df.reset_index(inplace=True)
            ohlc_df.columns = ["date", "open", "high", "low", "close", "volume"]
            ohlc_df["date"] = ohlc_df["date"].apply(lambda x: self.format_date(x))
            return ohlc_df
        except Exception as err:
            raise Exception("Some err message from get ohlcv: {}".format(str(err)))

    def market_order(self, inst, order_config={}):
        pass
