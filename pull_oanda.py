import json
import pandas as pd

import quantlib.data_utils as data_utils

from brokerage.oanda.oanda import Oanda
from subsystems.lbmom.subsys import Lbmom
from subsystems.lsmom.subsys import Lsmom
from dateutil.relativedelta import relativedelta


with open("config/auth_config.json") as f:
    auth_config = json.load(f)

with open("config/oan_config.json") as f:
    brokerage_config = json.load(f)

"""
THIS SCRIPT IS FOR WORKING WITH OANDA BROKER

In subsys for, both, lbmom and lsmom we should inside 'run_simulation()' method set
variable instruments to this -> instruments = self.instruments_config["indices"] + self.instruments_config['bonds'] (for our example)
"""

brokerage = Oanda(auth_config=auth_config)
trade_client = brokerage.get_trade_client()

db_instruments = (
    brokerage_config["currencies"]
    + brokerage_config["indices"]
    + brokerage_config["commodities"]
    + brokerage_config["metals"]
    + brokerage_config["bonds"]
)

oan_ohlcv = pd.DataFrame()
for db_inst in db_instruments:
    df = trade_client.get_ohlcv(
        instrument=db_inst, count=2500, granularity="D"
    ).set_index("date")
    cols = list(map(lambda x: f"{db_inst} {x}", df.columns))
    df.columns = cols
    if len(oan_ohlcv) == 0:
        oan_ohlcv = df
    else:
        oan_ohlcv = oan_ohlcv.combine_first(df)

historical_df = data_utils.extend_dataframe(
    traded=db_instruments, df=oan_ohlcv, fx_codes=brokerage_config["fx_codes"]
)

historical_df.to_excel("./Data/oanda/historical_df.xlsx")

VOL_TARGET = 0.2

simulation_start = historical_df.index[-1] - relativedelta(years=3)

lbmom_strat = Lbmom(
    instruments_config="./subsystems/lbmom/oan_instruments.json",
    historical_df=historical_df,
    simulation_start=simulation_start,
    vol_target=VOL_TARGET,
)

portfolio_lbmom_df, instruments = lbmom_strat.get_subsys_pos()
portfolio_lbmom_df.to_csv("./Data/oanda/lbmom_strat.csv")

lsmom_strat = Lsmom(
    instruments_config="./subsystems/lsmom/oan_instruments.json",
    historical_df=historical_df,
    simulation_start=simulation_start,
    vol_target=VOL_TARGET,
)

portfolio_lsmom_df, instruments = lsmom_strat.get_subsys_pos()
portfolio_lsmom_df.to_csv("./Data/oanda/lsmom_strat.csv")
