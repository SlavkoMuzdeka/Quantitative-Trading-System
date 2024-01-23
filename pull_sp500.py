import quantlib.data_utils as data_utils

from dateutil.relativedelta import relativedelta
from subsystems.lbmom.subsys import Lbmom
from subsystems.lsmom.subsys import Lsmom

"""
THIS SCRIPT IS FOR WORKING WITH SP500 instruments

In subsys for both lbmom and lsmom we should inside 'run_simulation()' method set
variable instruments to this -> instruments = self.instruments_config["instruments"]
"""

df, instruments = data_utils.get_sp500_df()
historical_df = data_utils.extend_dataframe(traded=instruments, df=df, fx_codes=[])
historical_df.to_excel("./Data/sp500/historical_df.xlsx")

VOL_TARGET = 0.2

simulation_start = historical_df.index[-1] - relativedelta(years=5)

lbmom_strat = Lbmom(
    instruments_config="./subsystems/lbmom/sp500_instruments.json",
    historical_df=historical_df,
    simulation_start=simulation_start,
    vol_target=VOL_TARGET,
)

portfolio_lbmom_df, instruments = lbmom_strat.get_subsys_pos()
portfolio_lbmom_df.to_csv("./Data/sp500/lbmom_strat.csv")

lsmom_strat = Lsmom(
    instruments_config="./subsystems/lsmom/sp500_instruments.json",
    historical_df=historical_df,
    simulation_start=simulation_start,
    vol_target=VOL_TARGET,
)

portfolio_lsmom_df, instruments = lsmom_strat.get_subsys_pos()
portfolio_lsmom_df.to_csv("./Data/sp500/lsmom_strat.csv")
