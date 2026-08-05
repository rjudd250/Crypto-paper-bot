import argparse
import time
import pandas as pd
import ccxt

from strategy import add_indicators, generate_signal


def fetch_ohlcv(symbol, timeframe, days):
    exchange = ccxt.binance()
    ms_per_candle = exchange.parse_timeframe(timeframe) * 1000
    limit = min(1000, int(days * 24 * 60 * 60 * 1000 / ms_per_candle))
    since = exchange.milliseconds() - days * 24 * 60 * 60 * 1000

    all_rows = []
    while True:
        batch = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not batch:
            break
        all_rows += batch
        since = batch[-1][0] + ms_per_candle
        if len(batch) < 1000:
            break
        time.sleep(exchange.rateLimit / 1000)

    df = pd.DataFrame(all_rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def run_backtest(df, starting_balance=1000.0, fee_pct=0.001):
    df = add_indicators(df)
    balance = starting_balance
    position = 0.0
    entry_price = None
    trades = []

    for i in range(2, len(df)):
        window = df.iloc[: i + 1]
        signal = generate_signal(window)
        price = df.iloc[i]["close"]
        ts = df.iloc[i]["timestamp"]

        if signal == "BUY" and position == 0:
            fee = balance * fee_pct
            position = (balance - fee) / price
            entry_price = price
            trades.append({"time": ts, "action": "BUY", "price": price, "balance": balance})
            balance = 0.0

        elif signal == "SELL" and position > 0:
            proceeds = position * price
            fee = proceeds * fee_pct
            balance = proceeds - fee
            pnl_pct = (price - entry_price) / entry_price * 100
            trades.append({"time": ts, "action": "SELL", "price": price, "balance": balance, "pnl_pct": pnl_pct})
            position = 0.0
            entry_price = None

    final_price = df.iloc[-1]["close"]
    final_value = balance + position * final_price

    trades_df = pd.DataFrame(trades)
    total_return_pct = (final_value - starting_balance) / starting_balance * 100
    num_round_trips = len(trades_df[trades_df["action"] == "SELL"]) if not trades_df.empty else 0
    win_rate = None
    if num_round_trips > 0:
        wins = (trades_df["pnl_pct"] > 0).sum()
        win_rate = wins / num_round_trips * 100

    print(f"Starting balance:  ${starting_balance:,.2f}")
    print(f"Final value:       ${final_value:,.2f}")
    print(f"Total return:      {total_return_pct:.2f}%")
    print(f"Number of trades:  {num_round_trips}")
    if win_rate is not None:
        print(f"Win rate:          {win_rate:.1f}%")

    hold_value = starting_balance / df.iloc[0]["close"] * final_price
    hold_return_pct = (hold_value - starting_balance) / starting_balance * 100
    print(f"\nBuy & hold return over same period: {hold_return_pct:.2f}%")

    trades_df.to_csv("data/backtest_trades.csv", index=False)
    print("\nTrade log saved to data/backtest_trades.csv")

    return trades_df, final_value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--balance", type=float, default=1000.0)
    args = parser.parse_args()

    print(f"Fetching {args.days}d of {args.timeframe} candles for {args.symbol}...")
    df = fetch_ohlcv(args.symbol, args.timeframe, args.days)
    print(f"Fetched {len(df)} candles.\n")

    run_backtest(df, starting_balance=args.balance)
