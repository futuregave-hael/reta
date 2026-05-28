# Bitcoin Analyzer (OpenBB + optional FinBERT/FinGPT sentiment)

A small CLI toolkit that uses the [OpenBB Platform](https://github.com/OpenBB-finance/OpenBB)
to fetch historical Bitcoin price data and compute standard technical
indicators, plus an **optional** sentiment module backed by
[FinBERT](https://huggingface.co/ProsusAI/finbert) (default) or
[FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) (LoRA, GPU-only).

> **Important:** This is NOT financial advice. No analysis can predict
> Bitcoin prices with certainty. The indicators here describe the recent
> past - they do not predict the future. Sentiment scores are noisy
> summaries of text; they are not signals to act on.

## What it does

**Technical analysis (`analyze.py`):**

- Fetches historical OHLCV data via OpenBB (default provider: `yfinance`)
- Computes:
  - SMA 20 / 50 / 200
  - RSI(14)
  - MACD (12, 26, 9)
  - Bollinger Bands (20, 2)
  - 30-day annualised volatility
  - Period high / low and rolling % changes
- Prints an objective text report with plain-language observations

**Sentiment analysis (`sentiment.py`, optional):**

- Default backend: **FinBERT** (`ProsusAI/finbert`, ~440 MB, runs on CPU)
- Optional backend: **FinGPT LoRA** (Llama2 base + LoRA adapter, requires GPU)
- Score inline texts, files, or stdin
- Per-text labels + an aggregate net score in `[-1, +1]`

## Setup

Python 3.10+ recommended.

```bash
cd btc_analyzer
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Core (technical analysis only)
pip install -r requirements.txt

# Optional: sentiment module
pip install -r requirements-sentiment.txt
```

## Usage

### Technical analysis

```bash
# Default: BTC-USD, 365 days, yfinance, daily candles
python analyze.py

# Custom range
python analyze.py --days 90

# Other crypto (anything supported by the chosen provider)
python analyze.py --symbol ETH-USD

# Export the raw OHLCV used in the analysis
python analyze.py --export btc.csv
```

### Sentiment analysis

```bash
# Score inline headlines
python sentiment.py \
    --text "Bitcoin spot ETF inflows hit record high" \
    --text "SEC delays Bitcoin ETF decision again" \
    --per-text

# Score a file (one headline per line). A sample is included.
python sentiment.py --file sample_headlines.txt --per-text

# JSON output, e.g. for piping
python sentiment.py --file sample_headlines.txt --json

# Pipe from another tool
some_news_fetcher | python sentiment.py
```

### Combined: TA report + sentiment

```bash
python analyze.py --news-file sample_headlines.txt
```

The technical report is printed first, followed by a sentiment summary block.

### FinGPT backend (optional, GPU only)

FinGPT is the heavyweight cousin of FinBERT and needs a CUDA GPU plus
access to a base Llama2 (or compatible) model. To use it:

```bash
# Uncomment `peft` in requirements-sentiment.txt, then:
pip install -r requirements-sentiment.txt

# Default base model and LoRA repo (override via flags or env vars)
export FINGPT_BASE_MODEL=meta-llama/Llama-2-7b-hf
export FINGPT_LORA_REPO=FinGPT/fingpt-sentiment_llama2-13b_lora

python sentiment.py --backend fingpt --file sample_headlines.txt
# or, in the combined report:
python analyze.py --news-file sample_headlines.txt --sentiment-backend fingpt
```

You will need a Hugging Face token with access to the gated Llama2
weights (`huggingface-cli login`).

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
information that does not yet exist. Sentiment models classify text
they have seen; they cannot read the market's mind. Use these signals
as inputs among many, not as a crystal ball.

## Extending

Ideas you can add later:
- More indicators (Stochastic, ATR, OBV, Ichimoku) via OpenBB's `obb.technical.*`
- Chart export with `matplotlib` or `plotly`
- On-chain metrics through OpenBB providers that support them
- Backtesting a simple rule (e.g. SMA crossover) on the fetched data
- Auto-fetching news headlines (RSS, NewsAPI, X/Twitter) into the sentiment pipeline
- Telegram / Discord / email alerts when RSI crosses thresholds or sentiment flips
