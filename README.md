pip install -r requirements.txt
python backtest.py –symbol BTC/USDT –timeframe 1h –days 180

This prints total return, number of trades, win rate, and a buy-and-hold
comparison so you can see whether the strategy actually beats just holding.
Try different symbols, timeframes, and date ranges — a strategy that only
looks good on one narrow window is not to be trusted.

Running paper trading manually

python paper_trade.py –symbol BTC/USDT –timeframe 15m –balance 1000

This fetches the latest candles, computes a signal, and updates
data/state.json (your virtual portfolio) and data/trade_log.csv
(a running history of every decision made).

Tuning the strategy

Open strategy.py and adjust:

fast / slow — the two moving average windows (default 10/30)
rsi_period — RSI lookback (default 14)
The RSI thresholds (70/30) that filter out overbought/oversold entries

Re-run backtest.py after every change before letting it run live in paper mode.

Checking in from your phone

View data/trade_log.csv and data/state.json any time from the GitHub mobile app or mobile browser — no need to be at a computer.
The Actions tab shows every run and its output.

Important notes

This is paper trading only. Turning this into real-money trading would require adding exchange API keys and real order placement — a significant jump in risk that isn’t part of this setup.
Crypto markets are volatile and this strategy has no guarantee of working even in simulation — the point of the backtest step is to see that honestly before you get attached to it.
Nothing here is financial advice.
