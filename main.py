import json
import pandas as pd
import datetime
import quantlib.general_utils as general_utils
import quantlib.data_utils as data_utils
import matplotlib.pyplot as plt

from subsystems.lbmom.subsys import Lbmom
from subsystems.lsmom.subsys import Lsmom
from dateutil.relativedelta import relativedelta
from brokerage.oanda.oanda import Oanda

# TODO CREATE THIS MODULES
# from brokerage.binance.binance import BinanceBroker as Broker
# from brokerage.kraken.kraken import KrakenBroker as Broker

with open("config/auth_config.json") as f:
    auth_config = json.load(f)

with open("config/portfolio_config.json") as f:
    portfolio_config = json.load(f)

with open("config/oan_config.json") as f:
    brokerage_config = json.load(f)

with open("config/crypto_config.json") as f:
    crypto_config = json.load(f)

brokerage = Oanda(auth_config=auth_config)
trade_client = brokerage.get_trade_client()

db_instruments = (
    brokerage_config["currencies"]
    + brokerage_config["indices"]
    + brokerage_config["commodities"]
    + brokerage_config["metals"]
    + brokerage_config["bonds"]
)


def run_strategies(historical_df, path):
    vol_target = portfolio_config["vol_target"]
    sim_start = datetime.date.today() - relativedelta(
        years=portfolio_config["sim_years"]
    )

    subsystems_config = portfolio_config["subsystems"]["oan"]
    strats = {}

    for subsystem in subsystems_config.keys():
        if subsystem == "lbmom":
            strat = Lbmom(
                instruments_config=portfolio_config["instruments_config"][subsystem][
                    "oan"
                ],
                historical_df=historical_df,
                simulation_start=sim_start,
                vol_target=vol_target,
            )
        elif subsystem == "lsmom":
            strat = Lsmom(
                instruments_config=portfolio_config["instruments_config"][subsystem][
                    "oan"
                ],
                historical_df=historical_df,
                simulation_start=sim_start,
                vol_target=vol_target,
            )
        else:
            print("Unknown strategy")
            exit()

        strats[subsystem] = strat

    for k, v in strats.items():
        # k, v pair is (subsystem, strat_object)
        strat_db, strat_inst = v.get_subsys_pos()
        strat_db.to_excel(f"{path}/{k}_strat.xlsx")


def main():
    """
    THIS CODE IS FOR WORKING WITH SP500 instruments

    1. In subsys for, both, lbmom and lsmom we should inside 'run_simulation()' method set
    variable instruments to this -> instruments = self.instruments_config["instruments"]
    """
    # historical_df = general_utils.load_file("./Data/sp500/historical_df.obj")
    # run_strategies(historical_df=historical_df, path="./Data/sp500")

    """
    THIS CODE IS FOR WORKING WITH OANDA BROKER
    1. In subsys for, both, lbmom and lsmom we should inside 'run_simulation()' method set
    variable instruments to this -> instruments = self.instruments_config["indices"] + self.instruments_config['bonds'] (for our example)

    2. If we want to have updated data, we should follow instructions below
    """

    # Comment this out, and uncomment lines below in production
    # database_df = general_utils.load_file("./Data/oanda/quick_ohlcv.obj")

    # database_df = pd.read_excel("./Data/oanda/oan_ohlcv.xlsx").set_index("date")
    # poll_df = pd.DataFrame()

    # for db_inst in db_instruments:
    #     df = trade_client.get_ohlcv(
    #         instrument=db_inst, count=30, granularity="D"
    #     ).set_index("date")
    #     cols = list(map(lambda x: f"{db_inst} {x}", df.columns))

    #     df.columns = cols
    #     if len(poll_df) == 0:
    #         poll_df[cols] = df
    #     else:
    #         poll_df = poll_df.combine_first(df)

    # database_df = database_df.loc[: poll_df.index[0]][:-1]
    # database_df = database_df._append(poll_df)
    # database_df.to_excel("./Data/oanda/oan_ohlcv.xlsx")

    """
    Extend dataframe with numerical statistics required for backtesting and alpha generation
    """

    # Because we are trading instruments from different currencies (denominated in different),
    # we need to do some FX conversion, so we will add more information required for fx conversion (we added fx_codes argument)
    # historical_data = data_utils.extend_dataframe(
    #     traded=db_instruments, df=database_df, fx_codes=brokerage_config["fx_codes"]
    # )
    # run_strategies(historical_df=historical_data, path="./Data/oanda")

    """
    THIS CODE IS FOR WORKING WITH CRYPTO TICKERS

    1. In subsys for, both, lbmom and lsmom we should inside 'run_simulation()' method set
    variable instruments to this -> instruments = self.instruments_config["crypto_tickers"] + self.instruments_config['crypto_tickers'] (for our example)

    """
    historical_df = general_utils.load_file("./Data/crypto/historical_df.obj")
    run_strategies(historical_df=historical_df, path="./Data/crypto")


if __name__ == "__main__":
    main()
