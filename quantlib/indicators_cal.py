import talib  # libraty for Technical Analysis


def adx_series(high, low, close, n):
    """
    This function calculates the Average Directional Index (ADX)
    based on the provided high, low and close price
    """
    return talib.ADX(high, low, close, timeperiod=n)


def ema_series(series, n):
    """
    This function calculates the Exponential Moving Average (EMA)
    based on a given input series.
    """
    return talib.EMA(series, timeperiod=n)


def sma_series(series, n):
    """
    This function calculates the Simple Moving Average (SMA)
    based on a given input series.
    """
    return talib.SMA(series, n)
