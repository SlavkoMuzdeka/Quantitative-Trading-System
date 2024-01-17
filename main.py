import json
import pandas as pd
import quantlib.general_utils as gu
from subsystems.lbmom.subsys import Lbmom

from dateutil.relativedelta import relativedelta

from brokerage.oanda.oanda import Oanda

with open("config/auth_config.json") as f:
    auth_config = json.load(f)

brokerage = Oanda(auth_config=auth_config)
trade_client = brokerage.get_trade_client()

# 1. Get summary details
# summary = trade_client.get_account_summary()
# print(json.dumps(summary, indent=4))

# 2. Get account capital
# account_capital = trade_client.get_account_capital()
# print(account_capital)

# 3. Get account details
# account_details = trade_client.get_account_details()
# print(json.dumps(account_details, indent=4))

# 4. Get account positions
# account_positions = trade_client.get_account_positions()
# print(json.dumps(account_positions, indent=4))

# 5. Get account trades
# account_trades = trade_client.get_account_trades()
# print(account_trades)

# 6. Get account instruments
instruments, fx, cfds, metals = trade_client.get_account_instruments()
# print(json.dumps(fx, indent=4))
# for i in fx:
#     is_tradable = trade_client.is_tradable(i)
#     print(i, is_tradable)

for i in fx:
    result = trade_client.get_ohlcv(instrument=i, count=100, granularity="D")
    exit()

exit()


# with open("config/oan_config.json") as f:
#     brokerage_config = json.load(f)

# brokerage = Oanda(auth_config=auth_config)

# db_instruments = (
#     brokerage_config["currencies"]
#     + brokerage_config["indices"]
#     + brokerage_config["commodities"]
#     + brokerage_config["metals"]
#     + brokerage_config["bonds"]
# )
# print(db_instruments)
# poll_df = pd.DataFrame()
# for db_inst in db_instruments:
#     df = brokerage.get_trade_client().get_ohlcv(
#         instrument=db_inst, count=250, granularity="D"
#     )
#     dataframes[db_inst] = df

# gu.save_file("dataframes.obj", dataframes)

# instruments, fx, cfds, metals = trade_client.get_account_instruments()

# fx_code = []
# for pair in fx:
#     fx_code.append(pair.split("_")[0])
#     fx_code.append(pair.split("_")[1])
# fx_codes = set(fx_code)
# config = {"fx_codes": list(fx_codes), "currencies": fx, "cfds": cfds, "metals": metals}

# with open("config/oan_config.json", "w") as f:
#     json.dump(config, f, indent=4)

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
