import json
import quantlib.data_utils as data_utils

from dateutil.relativedelta import relativedelta
from subsystems.lbmom.subsys import Lbmom
from subsystems.lsmom.subsys import Lsmom

with open("config/crypto_config.json") as f:
    crypto_config = json.load(f)

"""
THIS SCRIPT IS FOR WORKING WITH CRYPTO instruments

In subsys for both lbmom and lsmom we should inside 'run_simulation()' method set
variable instruments to this -> instruments = self.instruments_config["crypto_tickers"]
"""

df, instruments = data_utils.get_crypto_df(crypto_config=crypto_config)
historical_df = data_utils.extend_dataframe(traded=instruments, df=df, fx_codes=[])
historical_df.to_excel("./Data/crypto/historical_df.xlsx")
VOL_TARGET = 0.2

simulation_start = historical_df.index[-1] - relativedelta(years=3)

lbmom_strat = Lbmom(
    instruments_config="./subsystems/lbmom/crypto_instruments.json",
    historical_df=historical_df,
    simulation_start=simulation_start,
    vol_target=VOL_TARGET,
)

portfolio_lbmom_df, instruments = lbmom_strat.get_subsys_pos()
portfolio_lbmom_df.to_csv("./Data/crypto/lbmom_strat.csv")

lsmom_strat = Lsmom(
    instruments_config="./subsystems/lsmom/crypto_instruments.json",
    historical_df=historical_df,
    simulation_start=simulation_start,
    vol_target=VOL_TARGET,
)

portfolio_lsmom_df, instruments = lsmom_strat.get_subsys_pos()
portfolio_lsmom_df.to_csv("./Data/crypto/lsmom_strat.csv")
