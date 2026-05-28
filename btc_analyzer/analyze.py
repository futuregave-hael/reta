"""Bitcoin Analyzer using OpenBB Platform.

Fetches historical Bitcoin OHLCV data via OpenBB and computes a set of
standard technical indicators to produce an objective market snapshot.

This is NOT financial advice. Indicators are descriptive, not predictive.
No analysis can be 100% accurate - anyone claiming otherwise is misleading.

Usage:
    python analyze.py                       # default: 365 days, yfinance
    python analyze.py --days 90
    python analyze.py --symbol ETH-USD      # works for other crypto too
    python analyze.py --export prices.csv   # save raw data
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

try:
    from openbb import obb
except ImportError:
    print("ERROR: OpenBB not installed. Run: pip install -r requirements.txt")
    sys.exit(1)


# ----------------------------- data fetch ---------------------------------- #

def fetch_history(
    symbol: str = "BTC-USD",
    days: int = 365,
    provider: str = "yfinance",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch historical OHLCV data via OpenBB."""
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days)

    result = obb.crypto.price.historical(
        symbol=symbol,
        provider=provider,
        start_date=str(start),
        end_date=str(end),
        interval=interval,
    )
    df = result.to_df()
    if df.empty:
        raise RuntimeError(f"No data returned for {symbol}")
    # Normalise expected columns
    df.columns = [c.lower() for c in df.columns]
    return df


# ----------------------------- indicators ---------------------------------- #

def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def _bollinger(close: pd.Series, period: int = 20, num_std: float = 2.0):
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    return mid + num_std * std, mid, mid - num_std * std


def compute_indicators(df: pd.DataFrame) -> dict[str, Any]:
    close = df["close"]
    n = len(close)

    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    sma_200 = close.rolling(200).mean() if n >= 200 else None

    macd_line, signal_line, macd_hist = _macd(close)
    rsi = _rsi(close, 14)
    bb_up, bb_mid, bb_low = _bollinger(close, 20, 2.0)

    log_ret = np.log(close / close.shift(1))
    vol_30d_ann = float(log_ret.rolling(30).std().iloc[-1] * np.sqrt(365))

    last = -1

    def pct_change(periods: int) -> float | None:
        if n <= periods:
            return None
        return float((close.iloc[last] / close.iloc[last - periods] - 1) * 100)

    return {
        "as_of": df.index[last],
        "n_periods": n,
        "price": float(close.iloc[last]),
        "high_period": float(df["high"].max()),
        "low_period": float(df["low"].min()),
        "change_24h_pct": pct_change(1),
        "change_7d_pct": pct_change(7),
        "change_30d_pct": pct_change(30),
        "change_90d_pct": pct_change(90),
        "sma_20": float(sma_20.iloc[last]),
        "sma_50": float(sma_50.iloc[last]),
        "sma_200": float(sma_200.iloc[last]) if sma_200 is not None and not pd.isna(sma_200.iloc[last]) else None,
        "rsi_14": float(rsi.iloc[last]),
        "macd": float(macd_line.iloc[last]),
        "macd_signal": float(signal_line.iloc[last]),
        "macd_hist": float(macd_hist.iloc[last]),
        "bb_upper": float(bb_up.iloc[last]),
        "bb_mid": float(bb_mid.iloc[last]),
        "bb_lower": float(bb_low.iloc[last]),
        "volatility_30d_ann": vol_30d_ann,
    }


# ----------------------------- interpretation ------------------------------ #

def interpret(ind: dict[str, Any]) -> list[str]:
    """Plain-language observations. Descriptive only."""
    notes: list[str] = []
    price = ind["price"]

    if ind["sma_200"] is not None:
        rel = "ABOVE" if price > ind["sma_200"] else "BELOW"
        notes.append(
            f"Price is {rel} the 200-day SMA "
            f"(${ind['sma_200']:,.0f}) - long-term trend reference."
        )

    if ind["sma_20"] > ind["sma_50"]:
        notes.append("20-SMA above 50-SMA: short-term momentum is positive.")
    else:
        notes.append("20-SMA below 50-SMA: short-term momentum is negative.")

    rsi = ind["rsi_14"]
    if rsi >= 70:
        notes.append(f"RSI(14) = {rsi:.1f}: overbought zone (statistically extended).")
    elif rsi <= 30:
        notes.append(f"RSI(14) = {rsi:.1f}: oversold zone (statistically depressed).")
    else:
        notes.append(f"RSI(14) = {rsi:.1f}: neutral range.")

    if ind["macd"] > ind["macd_signal"]:
        notes.append(
            f"MACD ({ind['macd']:.2f}) above signal ({ind['macd_signal']:.2f}): "
            f"bullish crossover state."
        )
    else:
        notes.append(
            f"MACD ({ind['macd']:.2f}) below signal ({ind['macd_signal']:.2f}): "
            f"bearish crossover state."
        )

    bb_range = ind["bb_upper"] - ind["bb_lower"]
    if bb_range > 0:
        bb_pos = (price - ind["bb_lower"]) / bb_range
        if price > ind["bb_upper"]:
            notes.append("Price above upper Bollinger Band - statistically extended.")
        elif price < ind["bb_lower"]:
            notes.append("Price below lower Bollinger Band - statistically depressed.")
        else:
            notes.append(f"Price at {bb_pos * 100:.0f}% of Bollinger Band range.")

    notes.append(f"30-day annualised volatility: {ind['volatility_30d_ann'] * 100:.1f}%.")
    return notes


# ----------------------------- report -------------------------------------- #

def print_report(symbol: str, ind: dict[str, Any]) -> None:
    bar = "=" * 64
    sub = "-" * 64
    print(bar)
    print(f"  {symbol} MARKET SNAPSHOT")
    print(f"  As of: {ind['as_of']}    Periods analysed: {ind['n_periods']}")
    print(bar)

    def fmt(label: str, value: Any, unit: str = "", width: int = 14) -> str:
        if value is None:
            return f"  {label:<18} {'n/a':>{width}}"
        if unit == "$":
            return f"  {label:<18} ${value:>{width - 1},.2f}"
        if unit == "%":
            return f"  {label:<18} {value:>+{width}.2f} %"
        return f"  {label:<18} {value:>{width}.2f}"

    print()
    print(fmt("Price", ind["price"], "$"))
    print(fmt("Period high", ind["high_period"], "$"))
    print(fmt("Period low", ind["low_period"], "$"))
    print(fmt("24h change", ind["change_24h_pct"], "%"))
    print(fmt("7d change", ind["change_7d_pct"], "%"))
    print(fmt("30d change", ind["change_30d_pct"], "%"))
    print(fmt("90d change", ind["change_90d_pct"], "%"))
    print()
    print(fmt("SMA 20", ind["sma_20"], "$"))
    print(fmt("SMA 50", ind["sma_50"], "$"))
    print(fmt("SMA 200", ind["sma_200"], "$"))
    print()
    print(fmt("RSI(14)", ind["rsi_14"]))
    print(fmt("MACD", ind["macd"]))
    print(fmt("MACD signal", ind["macd_signal"]))
    print(fmt("MACD histogram", ind["macd_hist"]))
    print(fmt("BB upper", ind["bb_upper"], "$"))
    print(fmt("BB middle", ind["bb_mid"], "$"))
    print(fmt("BB lower", ind["bb_lower"], "$"))
    print(fmt("Vol 30d (ann.)", ind["volatility_30d_ann"] * 100, "%"))
    print()
    print(sub)
    print("  OBSERVATIONS  (descriptive, NOT predictive, NOT advice)")
    print(sub)
    for note in interpret(ind):
        print(f"  - {note}")
    print()
    print("  DISCLAIMER: Markets are uncertain. Technical indicators")
    print("  describe the recent past; they do not predict the future.")
    print("  This output is for educational use only - not investment advice.")
    print(bar)


# ----------------------------- entrypoint ---------------------------------- #

def main() -> None:
    p = argparse.ArgumentParser(description="Bitcoin (and crypto) analyser using OpenBB Platform.")
    p.add_argument("--symbol", default="BTC-USD", help="Symbol to analyse (default: BTC-USD)")
    p.add_argument("--days", type=int, default=365, help="Days of history (default: 365)")
    p.add_argument("--provider", default="yfinance", help="OpenBB data provider (default: yfinance)")
    p.add_argument("--interval", default="1d", help="Candle interval (default: 1d)")
    p.add_argument("--export", help="Optional path to export raw OHLCV CSV")
    args = p.parse_args()

    print(f"Fetching {args.symbol} history via OpenBB ({args.provider}, {args.interval})...")
    df = fetch_history(
        symbol=args.symbol,
        days=args.days,
        provider=args.provider,
        interval=args.interval,
    )
    print(f"Loaded {len(df)} rows. Range: {df.index.min()} -> {df.index.max()}\n")

    if args.export:
        df.to_csv(args.export)
        print(f"Raw data exported to {args.export}\n")

    ind = compute_indicators(df)
    print_report(args.symbol, ind)


if __name__ == "__main__":
    main()
