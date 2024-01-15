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
    symbols = get_sp500_instruments()
    symbols = symbols[:30]
    ohlcvs = {}  # o - open, h - high, l - low, c - close, v - volume
    for symbol in symbols:
        symbol_df = yf.Ticker(symbol).history(period="10y")
        ohlcvs[symbol] = symbol_df[["Open", "High", "Low", "Close", "Volume"]].rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
    df = pd.DataFrame(index=ohlcvs["AMZN"].index)
    df.index.name = "date"
    instruments = list(ohlcvs.keys())

    for inst in instruments:
        inst_df = ohlcvs[inst]
        # add an identifier to the columns
        columns = list(map(lambda x: "{} {}".format(inst, x), inst_df.columns))
        # add the instrument name to each column
        df[columns] = inst_df
    return df, instruments


def format_date(dates):
    yymmdd = list(map(lambda x: int(x), str(dates).split(" ")[0].split("-")))
    return datetime.date(yymmdd[0], yymmdd[1], yymmdd[2])


# takes an arbitrary dataframe with "inst o/h/l/c/v" and appends data + other numerical stats
# for use throuhgt the system
def extend_dataframe(traded, df):
    df.index = pd.Series(df.index).apply(
        lambda x: format_date(x)
    )  # puts all the index string dates into datetime object format
    open_cols = list(map(lambda x: str(x) + " open", traded))
    high_cols = list(map(lambda x: str(x) + " high", traded))
    low_cols = list(map(lambda x: str(x) + " low", traded))
    close_cols = list(map(lambda x: str(x) + " close", traded))
    volume_cols = list(map(lambda x: str(x) + " volume", traded))
    historical_data = df.copy()
    historical_data = historical_data[
        open_cols + high_cols + low_cols + close_cols + volume_cols
    ]
    historical_data.ffill(inplace=True)
    for inst in traded:
        # retrun statistics using closing prices and volatility statistics using rolling standard deviations of 25 day widow
        # we will check if a stock is being actively traded, by seeing if closing price today != yesterday
        historical_data["{} % ret".format(inst)] = (
            historical_data["{} close".format(inst)]
            / historical_data["{} close".format(inst)].shift(1)
            - 1
        )
        historical_data["{} % ret vol".format(inst)] = (
            historical_data["{} % ret".format(inst)].rolling(25).std()
        )
        historical_data["{} active".format(inst)] = historical_data[
            "{} close".format(inst)
        ] != historical_data["{} close".format(inst)].shift(1)
    historical_data.bfill(inplace=True)
    return historical_data


# df, instruments = get_sp500_df()
# historical_data = extend_dataframe(instruments, df)
# if "date" in df.index.names:
#     df.index = pd.to_datetime(df.index.get_level_values("date")).tz_convert(None)
#     df.to_excel("hist.xlsx")
#     print(historical_data)

# we have used backfill and forward fill functions to fill missing data
# for instance, some of the options for filling in missing data includes
"""
1. Forwardfill then Backfill
2. Brownian motion / Brownian Bridge
3. GARCH. GARCH variants and Copulas
4. Synthetic Data, such as through GAN and Stohastic Volatility Neural Networks
"""
