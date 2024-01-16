import quantlib.general_utils as gu
from subsystems.lbmom.subsys import Lbmom

from dateutil.relativedelta import relativedelta

(df, instruments) = gu.load_file("./Data/data.obj")
print(instruments)

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
