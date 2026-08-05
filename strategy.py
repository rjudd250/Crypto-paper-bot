import pandas as pd
import numpy as np


def add_indicators(df, fast=10, slow=30, rsi_period=14):
    df = df.copy()
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(rsi_period).mean()
    avg_loss = loss.rolling(rsi_period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50)

    return df


def generate_signal(df):
    if len(df) < 2:
        return "HOLD"

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    if pd.isna(prev["sma_fast"]) or pd.isna(prev["sma_slow"]):
        return "HOLD"

    crossed_up = prev["sma_fast"] <= prev["sma_slow"] and curr["sma_fast"] > curr["sma_slow"]
    crossed_down = prev["sma_fast"] >= prev["sma_slow"] and curr["sma_fast"] < curr["sma_slow"]

    if crossed_up and curr["rsi"] < 70:
        return "BUY"
    if crossed_down and curr["rsi"] > 30:
        return "SELL"
    return "HOLD"
