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


class Lsmom:
    """
    This class represents a strategy for backtesting and analyzing
    financial market data. Here we just copied and pasted the code from
    the lbmom and then edited the instruments traded and also the signal
    generation code (in the voting system)
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
        self.sysname = "LSMOM"
        with open(instruments_config) as f:
            self.instruments_config = json.load(f)

    def extend_historicals(self, instruments, historical_data):
        new_historical_data = historical_data.copy()

        for inst in instruments:
            # Calculate Average Directional Index (ADX)
            new_historical_data[f"{inst} adx"] = indicators_cal.adx_series(
                high=historical_data[inst + " high"],
                low=historical_data[inst + " low"],
                close=historical_data[inst + " close"],
                n=14,
            )

            # Create a list to store calculated EMA differences
            ema_differences = []

            # Calculate moving average crossover for each pair
            for pair in self.pairs:
                ema_difference = indicators_cal.ema_series(
                    series=historical_data[inst + " close"], n=pair[0]
                ) - indicators_cal.ema_series(
                    series=historical_data[inst + " close"], n=pair[1]
                )
                ema_differences.append(ema_difference)

            # Concatenate all EMA differences at once
            ema_difference_df = pd.concat(ema_differences, axis=1)
            ema_difference_df.columns = [
                f"{inst} ema{str(pair)}" for pair in self.pairs
            ]

            # Add the concatenated DataFrame to the new_historical_data
            new_historical_data = pd.concat(
                [new_historical_data, ema_difference_df], axis=1
            )

        return new_historical_data

    def run_simulation(self, historical_data, debug=False):
        """
        Init & Pre-process
        """
        instruments = self.instruments_config["instruments"]

        # Calculate/pre-process indicators
        historical_data = self.extend_historicals(
            instruments=instruments, historical_data=historical_data
        )
        historical_data.bfill(inplace=True)

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

            portfolio_df.loc[i, "strat scalar"] = strat_scalar

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
                ) + np.sum(
                    [
                        -1
                        for pair in self.pairs
                        if historical_data.loc[date, "{} ema{}".format(inst, str(pair))]
                        < 0
                    ]
                )
                forecast = votes / len(self.pairs)
                forecast = (
                    0
                    if historical_data.loc[date, "{} adx".format(inst)] < 25
                    else forecast
                )

                # volatility targetting
                position_vol_target = (
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
                )

                dollar_volatility = backtest_utils.unit_val_change(
                    inst, inst_price * percent_ret_vol, historical_data, date
                )
                position = (
                    strat_scalar * forecast * position_vol_target / dollar_volatility
                )
                portfolio_df.loc[i, "{} units".format(inst)] = position
                nominal_total += abs(
                    position
                    * backtest_utils.unit_dollar_value(inst, historical_data, date)
                )  # assuming all denominated in same currency

            for inst in tradable:
                units = portfolio_df.loc[i, "{} units".format(inst)]
                nominal_inst = abs(
                    units
                    * backtest_utils.unit_dollar_value(inst, historical_data, date)
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

            if debug:
                print(portfolio_df.loc[i])

        return portfolio_df, instruments

    def get_subsys_pos(self, debug=False):
        portfolio_df, instruments = self.run_simulation(
            historical_data=self.historical_df, debug=debug
        )
        return portfolio_df, instruments
