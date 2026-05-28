# Bitcoin Analyzer (OpenBB)

A small CLI tool that uses the [OpenBB Platform](https://github.com/OpenBB-finance/OpenBB)
to fetch historical Bitcoin price data and compute standard technical indicators.

> **Important:** This is NOT financial advice. No analysis can predict
> Bitcoin prices with certainty. The indicators here describe the recent
> past - they do not predict the future.

## What it does

- Fetches historical OHLCV data via OpenBB (default provider: `yfinance`)
- Computes:
  - SMA 20 / 50 / 200
  - RSI(14)
  - MACD (12, 26, 9)
  - Bollinger Bands (20, 2)
  - 30-day annualised volatility
  - Period high / low and rolling % changes
- Prints an objective text report with plain-language observations

## Setup

Python 3.10+ recommended.

```bash
cd btc_analyzer
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
# Default: BTC-USD, 365 days, yfinance, daily candles
python analyze.py

# Custom range
python analyze.py --days 90

# Other crypto (anything supported by the chosen provider)
python analyze.py --symbol ETH-USD

# Export the raw OHLCV used in the analysis
python analyze.py --export btc.csv

# Different OpenBB provider (requires the matching extension installed)
python analyze.py --provider yfinance
```

## Sample output (shape only)

```
================================================================
  BTC-USD MARKET SNAPSHOT
  As of: 2026-05-28 00:00:00    Periods analysed: 365
================================================================

  Price              $   xx,xxx.xx
  Period high        $   xx,xxx.xx
  ...
  RSI(14)                    xx.xx
  MACD                       xx.xx
  ...
----------------------------------------------------------------
  OBSERVATIONS  (descriptive, NOT predictive, NOT advice)
----------------------------------------------------------------
  - Price is ABOVE the 200-day SMA ...
  - 20-SMA above 50-SMA: short-term momentum is positive.
  - RSI(14) = xx.x: neutral range.
  ...
================================================================
```

## Why "no mistake" is impossible

Markets are influenced by sentiment, regulation, macro conditions,
liquidity flows, and news - none of which are deterministic. Technical
indicators are summary statistics of past prices; they cannot price in
information that does not yet exist. Use them as one input among many,
not as a crystal ball.

## Extending

Ideas you can add later:
- More indicators (Stochastic, ATR, OBV, Ichimoku) via OpenBB's `obb.technical.*`
- Chart export with `matplotlib` or `plotly`
- On-chain metrics through OpenBB providers that support them
- Backtesting a simple rule (e.g. SMA crossover) on the fetched data
- Telegram / Discord / email alerts when RSI crosses thresholds
