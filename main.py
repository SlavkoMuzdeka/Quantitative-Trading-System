import json
import quantlib.general_utils as gu
from subsystems.lbmom.subsys import Lbmom

from dateutil.relativedelta import relativedelta

from brokerage.oanda.oanda import Oanda

with open("config/auth_config.json") as f:
    auth_config = json.load(f)

brokerage = Oanda(auth_config=auth_config)
trade_client = brokerage.get_trade_client()
# summary = trade_client.get_account_summary()
# print(json.dumps(summary, indent=2))

# instruments, fx, cfds, metals = trade_client.get_account_instruments()

# for i in fx:
#     result = trade_client.get_ohlcv(instrument=i, count=100, granularity="D")
#     print(result)

# (df, instruments) = gu.load_file("./Data/data.obj")

# run the lbom strategy through the driver
# VOL_TARGET = 0.20  # we are targetting 20% annualized vol

# perform simulation for the past 5 years
# sim_start = df.index[-1] - relativedelta(years=5)

# start = Lbmom(
#     instruments_config="./subsystems/lbmom/config.json",
#     historical_df=df,
#     simulation_start=sim_start,
#     vol_target=VOL_TARGET,
# )
# start.get_subsys_pos()
