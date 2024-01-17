import json
import datetime
import quantlib.general_utils as gu
import quantlib.data_utils as du

from subsystems.lbmom.subsys import Lbmom
from dateutil.relativedelta import relativedelta
from brokerage.oanda.oanda import Oanda

with open("config/auth_config.json") as f:
    auth_config = json.load(f)

with open("config/portfolio_config.json") as f:
    portfolio_config = json.load(f)

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

"""
Risk Parameters
"""
vol_target = portfolio_config["vol_target"]
sim_start = datetime.date.today() - relativedelta(years=portfolio_config["sim_years"])

"""
Subsystem Positioning
"""

start = Lbmom(
    instruments_config="./subsystems/lbmom/config.json",
    historical_df=historical_data,
    simulation_start=sim_start,
    vol_target=vol_target,
)
portfolio_df = start.get_subsys_pos()
