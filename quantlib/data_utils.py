from io import StringIO

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup
import datetime


def get_sp500_instruments():
    """
    This function provides a conveninet way to retreive the ticker symbols of S&P 500
    companies from Wikipedia using web scaping
    """
    # Send a GET request to the Wikipedia page containing the S&P 500 companies list
    res = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    # Create a BeautifulSoup object to parse the HTML content of the page
    soup = BeautifulSoup(res.content, "lxml")
    # Find the first table on the page containing the list of S&P 500 companies
    table = soup.find_all("table")[0]
    # Use pandas read_html to extract tables from HTML and convert them to DataFrames
    df = pd.read_html(StringIO(str(table)))
    # Extract the "Symbol" column from the first DataFrame (assuming it's the S&P 500 list)
    return list(df[0]["Symbol"])


def get_sp500_df():
    """
    The method fetches historical OHLCV data fro a selected subset of S&P 500 symbols,
    organize the data and returns a DataFrame along with a list of instruments. The resulting
    DataFrame has columns uniquely identified by combining the instrument name and OHLCV type
    """
    symbols = get_sp500_instruments()
    symbols = symbols[:30]
    # Initialize a dictionary to store OHLCV (Open, High, Low, Close, Volume) data for each symbol
    ohlcvs = {}
    # Loop through each symbol, retrieve historical data, and store it in the dictionary
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
    # Create an empty DataFrame with the index of the historical data of Amazon (AMZN)
    df = pd.DataFrame(index=ohlcvs["AMZN"].index)
    df.index.name = "date"
    instruments = list(ohlcvs.keys())

    # Loop through each instrument, add identifier to columns, and append data to the DataFrame
    for inst in instruments:
        inst_df = ohlcvs[inst]
        # add an identifier to the columns
        columns = list(map(lambda x: "{} {}".format(inst, x), inst_df.columns))
        # add the instrument name to each column
        df[columns] = inst_df

    return df, instruments


def format_date(dates):
    """
    Function takes a data-like input, extracts the year, month and day and returns a
    'datetime.date' object representing that date. This can be useful for ensuring
    consistent object types when dealing with date-related operation in a program
    """
    yymmdd = list(map(lambda x: int(x), str(dates).split(" ")[0].split("-")))
    return datetime.date(yymmdd[0], yymmdd[1], yymmdd[2])


# takes an arbitrary dataframe with "inst o/h/l/c/v" and appends data + other numerical stats
# for use throuhgt the system
def extend_dataframe(traded, df, fx_codes):
    """
    Function extends a DataFrame containing OHLCV data for multiple instruments by adding
    columns with additional statistics related to percentage returns, return volatility
    and active trading indicators.
    """
    df.index = pd.Series(df.index).apply(
        lambda x: format_date(x)
    )  # puts all the index string dates into datetime object format

    open_cols = list(map(lambda x: str(x) + " open", traded))
    high_cols = list(map(lambda x: str(x) + " high", traded))
    low_cols = list(map(lambda x: str(x) + " low", traded))
    close_cols = list(map(lambda x: str(x) + " close", traded))
    volume_cols = list(map(lambda x: str(x) + " volume", traded))

    # Create a copy of the DataFrame and select relevant columns
    historical_data = df.copy()
    historical_data = historical_data[
        open_cols + high_cols + low_cols + close_cols + volume_cols
    ]

    # Forward fill missing values in the DataFrame
    historical_data.ffill(inplace=True)

    # Iterate through each instrument and calculate additional statistics
    for inst in traded:
        # Calculate percentage return
        historical_data["{} % ret".format(inst)] = (
            historical_data["{} close".format(inst)]
            / historical_data["{} close".format(inst)].shift(1)
            - 1
        )

        # Calculate percentage return volatility using a 25-day rolling standard deviation
        historical_data["{} % ret vol".format(inst)] = (
            historical_data["{} % ret".format(inst)].rolling(25).std()
        )

        # Check if the stock is actively traded by comparing closing prices today and yesterday
        historical_data["{} active".format(inst)] = historical_data[
            "{} close".format(inst)
        ] != historical_data["{} close".format(inst)].shift(1)

    # Back fill missing values in the DataFrame
    historical_data.bfill(inplace=True)
    return historical_data


# we have used backfill and forward fill functions to fill missing data
# for instance, some of the options for filling in missing data includes
"""
1. Forwardfill then Backfill
2. Brownian motion / Brownian Bridge
3. GARCH. GARCH variants and Copulas
4. Synthetic Data, such as through GAN and Stohastic Volatility Neural Networks
"""
