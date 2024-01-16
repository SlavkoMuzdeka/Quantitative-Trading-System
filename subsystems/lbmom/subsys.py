import numpy as np
import pandas as pd
import json
import quantlib.indicators_cal as indicators_cal
import quantlib.backtest_utils as backtest_utils

"""
# About volatility read this post: 

1. https://hangukquant.substack.com/p/volatility-targeting-the-asset-level
2. https://hangukquant.substack.com/p/volatility-targeting-the-strategy
"""


class Lbmom:
    """
    This class represents a strategy for backtesting and analyzing
    financial market data
    """

    def __init__(self, instruments_config, historical_df, simulation_start, vol_target):
        self.pairs = self.pairs = [
            (32, 155),
            (218, 234),
            (29, 53),
            (51, 81),
            (204, 248),
            (76, 129),
            (48, 195),
            (99, 104),
            (94, 158),
            (56, 205),
            (103, 217),
            (21, 150),
            (117, 217),
            (270, 283),
            (154, 283),
            (129, 282),
            (29, 224),
            (31, 143),
            (103, 218),
            (153, 269),
            (42, 146),
        ]
        self.historical_df = historical_df
        self.simulation_start = simulation_start
        self.vol_target = vol_target
        self.sysname = "LBMOM"
        with open(instruments_config) as f:
            self.instruments_config = json.load(f)

    # A function to get extra indicators specific to this strategy
    # A function to run a backtest/get positions from this strategy

    def extend_historicals(self, instruments, historical_data):
        # this will be the moving average crossover, such that if the fastMA crossover the slowMA, then it is a buy
        # a long-biased momentum strategy is biased in the long direction, so this will be a 100/0 L/S strategy
        # we also use a filter to identify false positive signals (we use the average directional index, or the adx)

        for inst in instruments:
            # Calculate Average Directional Index (ADX)
            historical_data["{} adx".format(inst)] = indicators_cal.adx_series(
                high=historical_data[inst + " high"],
                low=historical_data[inst + " low"],
                close=historical_data[inst + " close"],
                n=14,
            )
            # Calculate moving average crossover for each pair
            for pair in self.pairs:
                historical_data[
                    "{} ema{}".format(inst, str(pair))
                ] = indicators_cal.ema_series(
                    series=historical_data[inst + " close"], n=pair[0]
                ) - indicators_cal.ema_series(
                    series=historical_data[inst + " close"], n=pair[1]
                )  # fastMA - slowMA
        return historical_data

    def run_simulation(self, historical_data):
        # Initialization
        instruments = self.instruments_config["instruments"]

        # Calculate/pre-process indicators
        historical_data = self.extend_historicals(
            instruments=instruments, historical_data=historical_data
        )

        # Perform simulation
        portfolio_df = pd.DataFrame(
            index=historical_data[self.simulation_start :].index
        ).reset_index()
        portfolio_df.loc[0, "capital"] = 10000

        # Define a function to check if an instrument is halted from trading
        is_halted = (
            lambda inst, date: not np.isnan(
                historical_data.loc[date, "{} active".format(inst)]
            )
            and (~historical_data[:date].tail(5)["{} active".format(inst)]).all()
        )
        # recall that active is when the closing price of today is different from yesterday
        # if it is not changing for more than 5 days, consider it to be halted from trading
        # exclude it from the trading universe or assign weight to 0

        """
        Position Sizing with 3 different techniques combined:
            1. Strategy Level scalar for strategy level risk exposure
            2. Volatility targeting scalar for different assets
            3. Voting system to account for degree of 'momentum'
        """
        # Loop through each date in the simulation period
        for i in portfolio_df.index:
            date = portfolio_df.loc[i, "date"]
            strat_scalar = 2  # default scaling up for strategy

            # Get the list of tradable and non-tradable instruments
            tradable = [inst for inst in instruments if not is_halted(inst, date)]
            non_tradable = [inst for inst in instruments if inst not in tradable]

            """
            Get PnL and Scalar for Portfolio
            """
            if i != 0:
                date_prev = portfolio_df.loc[i - 1, "date"]
                pnl = backtest_utils.get_backtest_day_stats(
                    portfolio_df, instruments, date, date_prev, i, historical_data
                )
                strat_scalar = backtest_utils.get_strat_scalar(
                    portfolio_df, 100, self.vol_target, i, strat_scalar
                )

            """
            Get Positions for Traded Instruments, Assign 0 to Non-Traded
            """
            for inst in non_tradable:
                portfolio_df.loc[i, "{} units".format(inst)] = 0
                portfolio_df.loc[i, "{} w".format(inst)] = 0

            nominal_total = 0
            for inst in tradable:
                # Calculate the number of votes based on certain conditions
                votes = np.sum(
                    [
                        1
                        for pair in self.pairs
                        if historical_data.loc[date, "{} ema{}".format(inst, str(pair))]
                        > 0
                    ]
                )
                forecast = votes / len(
                    self.pairs
                )  # 1 is all 'trending', 0 is none 'trending'

                # check if regime is trending else cast 0 vote for all, if adx < 25, consider as 'non trending'
                forecast = (
                    0
                    if historical_data.loc[date, "{} adx".format(inst)] < 25
                    else forecast
                )

                # volatility targetting
                position_target = (
                    (1 / len(tradable))
                    * portfolio_df.loc[i, "capital"]
                    * self.vol_target
                    / np.sqrt(253)
                )

                inst_price = historical_data.loc[date, "{} close".format(inst)]
                percent_ret_vol = (
                    historical_data.loc[date, "{} % ret vol".format(inst)]
                    if historical_data[:date].tail(25)["{} active".format(inst)].all()
                    else 0.025
                )  # it says if the stock has been actively traded in the last 25 days for all days,
                # then use the rolling volatility of stock returns, else use 2.5%. Why? Imagine if the stock
                # is not active, trades like 1 1 1 1 1 2 1 1 1 1 2 1 1 1 and barely moves being halted on most days.
                # This would blow up the standard deviation and if sizing is proportional to 1/std, then small std
                # indicates postion blows up
                # this is a risk hazard
                dollar_volatility = inst_price * percent_ret_vol  # vol in dollar terms
                position = strat_scalar * forecast * position_target / dollar_volatility
                portfolio_df.loc[i, "{} units".format(inst)] = position
                nominal_total += abs(
                    position * inst_price
                )  # assuming all denominated in same currency

            for inst in tradable:
                units = portfolio_df.loc[i, "{} units".format(inst)]
                nominal_inst = abs(
                    units * historical_data.loc[date, "{} close".format(inst)]
                )
                inst_w = nominal_inst / nominal_total
                portfolio_df.loc[i, "{} w".format(inst)] = inst_w

            """
            Perform Logging and Calculations
            """
            portfolio_df.loc[i, "nominal"] = nominal_total
            portfolio_df.loc[i, "leverage"] = (
                portfolio_df.loc[i, "nominal"] / portfolio_df.loc[i, "capital"]
            )
        return portfolio_df

    def get_subsys_pos(self):
        self.run_simulation(historical_data=self.historical_df)


# from our main driver, we pass the dataframe into the LBMOM strategy, than let the LBMOM perform some
# calculations using the quantlib indicators calculator
# after the calculations, we pass into the simulator, where we can run some simulations and backtesting

# we don't perform unnecessary calculations - we do general calc in the driver, such as returns. volatility etc
# needed for all strategies then, indicators specific to start is done inside the strategy to save time
# each strategy has a config file, so that we can control some parameters

# we are also adopting a risk management technique at the asset and strategy level called
# vol targeting, where we laver out capital in order to achieve a certain 'target' annualized
# volatility and the relative allocations are inversely proportional to the volatility of the asset

# the reasoning is simple: assume volatility is a proxy for risk, we want to assign a similar
# amount of 'risk' to each position. We do not want any particular position to have outsized
# impacts on the overall portfolio, hence the term volatility targetting
