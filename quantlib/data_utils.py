from io import StringIO

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup
import datetime


def get_sp500_instruments():
    res = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(res.content, "lxml")
    table = soup.find_all("table")[0]
    df = pd.read_html(StringIO(str(table)))

    return list(df[0]["Symbol"])


def get_sp500_df():
    symbols = get_sp500_instruments()[:30]
    return get_df(symbols, index_ticker="AMZN", period="5y")


def get_crypto_df(crypto_config):
    return get_df(
        symbols=crypto_config["crypto_tickers"], index_ticker="BTC-USD", period="5y"
    )


def extend_dataframe(traded, df, fx_codes):
    """
    Function extends a DataFrame containing OHLCV data for multiple instruments by adding
    columns with additional statistics related to percentage returns, return volatility
    and active trading indicators.
    """
    df.index = pd.Series(df.index).apply(lambda x: format_date(x))

    open_cols = list(map(lambda x: str(x) + " open", traded))
    high_cols = list(map(lambda x: str(x) + " high", traded))
    low_cols = list(map(lambda x: str(x) + " low", traded))
    close_cols = list(map(lambda x: str(x) + " close", traded))
    volume_cols = list(map(lambda x: str(x) + " volume", traded))

    historical_data = df.copy()

    historical_data = historical_data[
        open_cols + high_cols + low_cols + close_cols + volume_cols
    ]

    # Forward and back fill missing values in the DataFrame
    historical_data.ffill(inplace=True)
    historical_data.bfill(inplace=True)

    # Iterate through each instrument and calculate additional statistics
    for inst in traded:
        # Calculate percentage return (it divides the closing price of the current day by the closing price of the previous day)
        # Subtraction by 1 is a common practice in financial calculations to express return as a percentage change
        historical_data[f"{inst} % ret"] = (
            historical_data[f"{inst} close"] / historical_data[f"{inst} close"].shift(1)
            - 1
        )

        # Calculate percentage return volatility using a 25-day rolling standard deviation
        # The rolling window is applied to the daily percentage returns and at each position
        # it considers the previous 25 values, including the current one
        historical_data[f"{inst} % ret vol"] = (
            historical_data[f"{inst} % ret"].rolling(25).std()
        )

        # Check if the stock is actively traded by comparing closing prices today and yesterday
        historical_data[f"{inst} active"] = historical_data[
            f"{inst} close"
        ] != historical_data[f"{inst} close"].shift(1)

        if is_fx(inst, fx_codes):
            inst_rev = "{}_{}".format(inst.split("_")[1], inst.split("_")[0])
            historical_data[f"{inst_rev} close"] = 1 / historical_data[f"{inst} close"]
            historical_data[f"{inst_rev} % ret"] = (
                historical_data[f"{inst_rev} close"]
                / historical_data[f"{inst_rev} close"].shift(1)
                - 1
            )
            historical_data[f"{inst_rev} % ret vol"] = (
                historical_data[f"{inst_rev} % ret"].rolling(25).std()
            )

            historical_data[f"{inst_rev} active"] = historical_data[
                f"{inst_rev} close"
            ] != historical_data[f"{inst_rev} close"].shift(1)
    historical_data.bfill(inplace=True)
    return historical_data


def is_fx(inst, fx_codes):
    # e.g EUR_USD, USD_SGD
    return (
        len(inst.split("_")) == 2
        and inst.split("_")[0] in fx_codes
        and inst.split("_")[1] in fx_codes
    )


def format_date(dates):
    yymmdd = list(map(lambda x: int(x), str(dates).split(" ")[0].split("-")))
    return datetime.date(yymmdd[0], yymmdd[1], yymmdd[2])


def get_df(symbols, index_ticker, period="1y"):
    ohlcvs = {}
    for symbol in symbols:
        symbol_df = yf.Ticker(symbol).history(period=period)

        ohlcvs[symbol] = symbol_df[["Open", "High", "Low", "Close", "Volume"]].rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )

    df = pd.DataFrame(index=ohlcvs[index_ticker].index)
    df.index.name = "date"
    instruments = list(ohlcvs.keys())

    for inst in instruments:
        inst_df = ohlcvs[inst]
        columns = list(map(lambda x: f"{inst} {x}", inst_df.columns))
        df = pd.concat(
            [df, inst_df.rename(columns=dict(zip(inst_df.columns, columns)))], axis=1
        )
    df.index.name = "date"

    return df, instruments
