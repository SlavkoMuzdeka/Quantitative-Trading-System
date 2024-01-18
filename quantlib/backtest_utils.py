import numpy as np


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

    for inst in instruments:
        previous_holdings = portfolio_df.loc[date_idx - 1, "{} units".format(inst)]
        if previous_holdings != 0:
            price_change = (
                historical_data.loc[date, "{} close".format(inst)]
                - historical_data.loc[date_prev, "{} close".format(inst)]
            )
            dollar_change = unit_val_change(
                from_prod=inst,
                val_change=price_change,
                historical_data=historical_data,
                date=date_prev,
            )
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
        portfolio_df.loc[:idx].dropna().tail(lookback)["strat scalar"]
    )
    if len(capital_ret_history) == lookback:  # enough data
        annualized_vol = capital_ret_history.std() * np.sqrt(253)
        scalar_hist_avg = np.mean(strat_scaler_history)
        strat_scalar = scalar_hist_avg * vol_target / annualized_vol
        return strat_scalar
    else:
        return default


# Calculate the value change for a single unit
def unit_val_change(from_prod, val_change, historical_data, date):
    is_denominated = (
        len(from_prod.split("_")) == 2
    )  # for example. AAPl is not denominated, assume USD
    if not is_denominated:
        return val_change
    elif is_denominated and from_prod.split("_")[1] == "USD":
        return val_change
    else:
        return (
            val_change
            * historical_data.loc[date, "{}_USD close".format(from_prod.split("_")[1])]
        )


# The contract dollar value in base currency of the from_prod
def unit_dollar_value(from_prod, historical_data, date):
    is_denominated = len(from_prod.split("_")) == 2
    if (
        not is_denominated
    ):  # e.g. AAPL, GOOGL: 1 contract of AAPL is worth the price of AAPL
        return historical_data.loc[date, from_prod + " close"]
    if is_denominated and from_prod.split("_")[0] == "USD":  # e.g. USD_JPY, USD_MXN
        # the good or the bad thing that is being bought is 1 unit of USD, therefore one unit is worth 1 USD
        return 1
    if is_denominated and not from_prod.split("_")[0] == "USD":
        # HK33_HKD -> one contract is worth that price in HKD, convert OR
        # EUR_USD etc
        # so x_y means one contract of x in y dollars
        # so in USD terms, the dollar value of the contract is x * y_USD
        # i.e. HK33_HKD = 5HKD
        # in dollar terms, 5HKD * HKD/USD
        # i.e. EUR/USD = x >> x * USD/USD = x
        unit_price = historical_data.loc[date, from_prod + " close"]
        fx_inst = "{}_{}".format(from_prod.split("_")[1], "USD")
        fx_quote = (
            1 if fx_inst == "USD_USD" else historical_data.loc[date, fx_inst + " close"]
        )
        return unit_price * fx_quote
