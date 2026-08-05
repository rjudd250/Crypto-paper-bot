import argparse
import json
import os
from datetime import datetime, timezone

import pandas as pd
import ccxt

from strategy import add_indicators, generate_signal

STATE_PATH = "data/state.json"
LOG_PATH = "data/trade_log.csv"


def load_state(starting_balance):
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"balance": starting_balance, "position": 0.0, "entry_price": None}


def save_state(state):
    os.makedirs("data", exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def log_trade(row):
    os.makedirs("data", exist_ok=True)
    df_row = pd.DataFrame([row])
    if os.path.exists(LOG_PATH):
        df_row.to_csv(LOG_PATH, mode="a", header=False, index=False)
    else:
        df_row.to_csv(LOG_PATH, index=False)


def fetch_recent(symbol, timeframe, limit=200):
    exchange = ccxt.binance()
    raw = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def run_once(symbol, timeframe, starting_balance, fee_pct=0.001):
    df = fetch_recent(symbol, timeframe)
    df = add_indicators(df)
    signal = generate_signal(df)
    price = df.iloc[-1]["close"]
    now = datetime.now(timezone.utc).isoformat()

    state = load_state(starting_balance)
    action_taken = "HOLD"

    if signal == "BUY" and state["position"] == 0:
        fee = state["balance"] * fee_pct
        state["position"] = (state["balance"] - fee) / price
        state["entry_price"] = price
        state["balance"] = 0.0
        action_taken = "BUY"

    elif signal == "SELL" and state["position"] > 0:
        proceeds = state["position"] * price
        fee = proceeds * fee_pct
        state["balance"] = proceeds - fee
        state["position"] = 0.0
        state["entry_price"] = None
        action_taken = "SELL"

    portfolio_value = state["balance"] + state["position"] * price

    save_state(state)
    log_trade({
        "time": now,
        "symbol": symbol,
        "price": price,
        "signal": signal,
        "action_taken": action_taken,
        "balance": state["balance"],
        "position": state["position"],
        "portfolio_value": portfolio_value,
    })

    print(f"[{now}] {symbol} price={price:.2f} signal={signal} action={action_taken} "
          f"portfolio_value=${portfolio_value:,.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--balance", type=float, default=1000.0)
    args = parser.parse_args()

    run_once(args.symbol, args.timeframe, args.balance)
