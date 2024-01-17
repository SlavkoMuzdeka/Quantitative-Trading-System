import json
import pandas as pd
import quantlib.general_utils as gu
import quantlib.data_utils as du
from subsystems.lbmom.subsys import Lbmom

from dateutil.relativedelta import relativedelta

from brokerage.oanda.oanda import Oanda

with open("config/auth_config.json") as f:
    auth_config = json.load(f)

with open("config/oan_config.json") as f:
    brokerage_config = json.load(f)

brokerage = Oanda(auth_config=auth_config)
trade_client = brokerage.get_trade_client()

db_instruments = (
    brokerage_config["currencies"]
    + brokerage_config["indices"]
    + brokerage_config["commodities"]
    + brokerage_config["metals"]
    + brokerage_config["bonds"]
)

"""
Load and Update Database
"""
database_df = gu.load_file("./Data/quick_ohlcv.obj")

# database_df = pd.read_excel("./Data/oan_ohlcv.xlsx").set_index("date")
# poll_df = pd.DataFrame()

# for db_inst in db_instruments:
#     df = trade_client.get_ohlcv(
#         instrument=db_inst, count=30, granularity="D"
#     ).set_index("date")
#     cols = list(map(lambda x: "{} {}".format(db_inst, x), df.columns))
#     df.columns = cols
#     if len(poll_df) == 0:
#         poll_df[cols] = df
#     else:
#         poll_df = poll_df.combine_first(df)

# database_df = database_df.loc[: poll_df.index[0]][:-1]
# database_df = database_df._append(poll_df)
# database_df.to_excel("./Data/oan_ohlcv.xlsx")

historical_data = du.extend_dataframe(
    traded=db_instruments, df=database_df, fx_codes=brokerage_config["fx_codes"]
)

exit()
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
# instruments, fx, cfds, metals = trade_client.get_account_instruments()
# print(json.dumps(fx, indent=4))
# for i in fx:
#     is_tradable = trade_client.is_tradable(i)
#     print(i, is_tradable)

# for i in fx:
#     result = trade_client.get_ohlcv(instrument=i, count=100, granularity="D")
#     exit()

# 7.
# fx_code = []
# for pair in fx:
#     fx_code.append(pair.split("_")[0])
#     fx_code.append(pair.split("_")[1])
# fx_codes = set(fx_code)

# config = {"fx_codes": list(fx_codes), "currencies": fx, "cfds": cfds, "metals": metals}
# with open("config/oan_config.json", "w") as f:
#     json.dump(config, f, indent=4)

# run the lbom strategy through the driver
VOL_TARGET = 0.20  # we are targetting 20% annualized vol

# perform simulation for the past 5 years
sim_start = df.index[-1] - relativedelta(years=5)

start = Lbmom(
    instruments_config="./subsystems/lbmom/config.json",
    historical_df=df,
    simulation_start=sim_start,
    vol_target=VOL_TARGET,
)
start.get_subsys_pos()
