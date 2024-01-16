import numpy as np
import pandas as pd


def get_backtest_day_stats(
    portfolio_df, instruments, date, date_prev, date_idx, historical_data
):
    """
    This function is used in the context of backtesting a trading strategy. It calculates various
    statistics for a given day in the backtest. Purpose:
    1. Calculate the daily profit and loss ('day_pnl') for each instrument
    2. Calculate the nominal return ('nominal_ret') for each instrument
    3. Update the portfolio DataFrame with relevant statistics for the current date
    """
    day_pnl = 0
    nominal_ret = 0
    # there are 2 ways we can do this, either using each position sizing or through vector operation
    # for clarity, we can use the longer, slower method
    for inst in instruments:
        previous_holdings = historical_data.loc[date_idx - 1, "{} units".format(inst)]
        if previous_holdings != 0:
            price_change = (
                historical_data.loc[date, "{} close".format(inst)]
                - historical_data.loc[date_prev, "{} close".format(inst)]
            )
            # do some fx conversion if not in dollars
            dollar_change = price_change * 1  # since all in USD
            inst_pnl = dollar_change * previous_holdings
            day_pnl += inst_pnl
            nominal_ret += (
                portfolio_df.loc[date_idx - 1, "{} w".format(inst)]
                * historical_data.loc[date, "{} % ret".format(inst)]
            )
    capital_ret = nominal_ret * portfolio_df.loc[date_idx - 1, "leverage"]
    portfolio_df.loc[date_idx, "capital"] = (
        portfolio_df.loc[date_idx - 1, "capital"] + day_pnl
    )
    portfolio_df.loc[date_idx, "daily pnl"] = day_pnl
    portfolio_df.loc[date_idx, "nominal ret"] = nominal_ret
    portfolio_df.loc[date_idx, "capital ret"] = capital_ret
    return day_pnl


def get_strat_scalar(portfolio_df, lookback, vol_target, idx, default):
    """
    This function calculates a scaling factor ('strat_scalar') based on historical capital
    returns to achieve a target volatility. Purpose:
    1. Calculate the annualized volatility of historical capital returns
    2. Calculate a scaling factor (strat_scalar) based on historical data
       to achieve the target volatility
    """
    capital_ret_history = portfolio_df.loc[:idx].dropna().tail(lookback)["capital ret"]
    strat_scaler_history = (
        portfolio_df.loc[:idx].dropna().tail(lookback)["strat scaler"]
    )
    if len(capital_ret_history) == lookback:  # enough data
        annualized_vol = capital_ret_history.std() * np.sqrt(253)
        scalar_hist_avg = np.mean(strat_scaler_history)
        strat_scalar = scalar_hist_avg * vol_target / annualized_vol
        return strat_scalar
    else:
        return default
