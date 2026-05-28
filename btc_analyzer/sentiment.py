"""Crypto / financial text sentiment analyser.

Default backend: FinBERT (ProsusAI/finbert) - small, CPU-friendly,
the practical sibling of FinGPT for sentiment classification.

Optional backend: FinGPT LoRA - heavier, requires a CUDA GPU and a
base Llama/ChatGLM model. See README for setup.

Sentiment is a NOISY signal. Treat it as one input among many,
never as a prediction. NOT financial advice.

Usage:
    # Score inline texts
    python sentiment.py --text "BTC ETF inflows hit record high" \
                        --text "SEC delays Bitcoin ETF decision again"

    # Score a file (one headline per line)
    python sentiment.py --file headlines.txt --per-text

    # JSON output for piping
    python sentiment.py --file headlines.txt --json

    # Use FinGPT LoRA backend (requires GPU + base model access)
    python sentiment.py --backend fingpt --file headlines.txt
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any

DEFAULT_FINBERT_MODEL = "ProsusAI/finbert"
DEFAULT_FINGPT_BASE = "meta-llama/Llama-2-7b-hf"
DEFAULT_FINGPT_LORA = "FinGPT/fingpt-sentiment_llama2-13b_lora"
LABELS = ("positive", "negative", "neutral")


# --------------------------- backends -------------------------------------- #

def _load_finbert(model_name: str = DEFAULT_FINBERT_MODEL):
    try:
        import torch
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            pipeline,
        )
    except ImportError as exc:
        raise RuntimeError(
            "FinBERT backend needs `transformers` and `torch`. "
            "Install with: pip install -r requirements-sentiment.txt"
        ) from exc

    device = 0 if torch.cuda.is_available() else -1
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    return pipeline(
        "sentiment-analysis",
        model=model,
        tokenizer=tokenizer,
        device=device,
        truncation=True,
        max_length=512,
        top_k=None,  # return all class scores
    )


def _score_finbert(texts: list[str], model_name: str) -> list[dict]:
    pipe = _load_finbert(model_name)
    raw = pipe(texts)  # list[list[{label, score}]]
    out: list[dict] = []
    for text, scores in zip(texts, raw):
        scores_lc = [{"label": s["label"].lower(), "score": float(s["score"])} for s in scores]
        best = max(scores_lc, key=lambda s: s["score"])
        out.append({
            "text": text,
            "label": best["label"],
            "score": best["score"],
            "all_scores": {s["label"]: s["score"] for s in scores_lc},
        })
    return out


def _load_fingpt(base_model: str, lora_repo: str):
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "FinGPT backend needs `transformers`, `torch`, and `peft`. "
            "Install with: pip install -r requirements-sentiment.txt"
        ) from exc

    if not torch.cuda.is_available():
        raise RuntimeError("FinGPT LoRA backend requires a CUDA GPU.")

    tok = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base, lora_repo)
    model.eval()
    return tok, model


def _score_fingpt(texts: list[str], base_model: str, lora_repo: str) -> list[dict]:
    import torch

    tok, model = _load_fingpt(base_model, lora_repo)
    out: list[dict] = []
    for text in texts:
        prompt = (
            "Instruction: What is the sentiment of this news? "
            "Please choose an answer from {negative/neutral/positive}.\n"
            f"Input: {text}\nAnswer: "
        )
        tokens = tok(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            gen = model.generate(**tokens, max_new_tokens=10, do_sample=False)
        answer = tok.decode(
            gen[0][tokens.input_ids.shape[1]:],
            skip_special_tokens=True,
        ).strip().lower()
        label = next((c for c in LABELS if c in answer), "neutral")
        out.append({
            "text": text,
            "label": label,
            "score": 1.0,  # FinGPT LoRA does not expose calibrated probabilities here
            "all_scores": None,
        })
    return out


# --------------------------- public API ------------------------------------ #

def score_texts(
    texts: list[str],
    backend: str = "finbert",
    model_name: str | None = None,
    base_model: str | None = None,
    lora_repo: str | None = None,
) -> list[dict]:
    """Score texts and return per-text {text, label, score, all_scores}."""
    cleaned = [t.strip() for t in texts if t and t.strip()]
    if not cleaned:
        return []

    if backend == "finbert":
        return _score_finbert(cleaned, model_name or DEFAULT_FINBERT_MODEL)
    if backend == "fingpt":
        base = base_model or os.getenv("FINGPT_BASE_MODEL", DEFAULT_FINGPT_BASE)
        lora = lora_repo or os.getenv("FINGPT_LORA_REPO", DEFAULT_FINGPT_LORA)
        return _score_fingpt(cleaned, base, lora)
    raise ValueError(f"Unknown backend: {backend!r}. Use 'finbert' or 'fingpt'.")


def aggregate(results: list[dict]) -> dict[str, Any]:
    """Aggregate a list of per-text scores into a summary."""
    if not results:
        return {"count": 0}

    counts = Counter(r["label"] for r in results)
    total = len(results)

    # Net score in [-1, +1], weighted by per-item confidence
    sign_map = {"positive": 1, "negative": -1, "neutral": 0}
    net = sum(sign_map.get(r["label"], 0) * r["score"] for r in results) / total

    return {
        "count": total,
        "positive": counts.get("positive", 0),
        "neutral": counts.get("neutral", 0),
        "negative": counts.get("negative", 0),
        "net_score": net,
        "label_majority": counts.most_common(1)[0][0],
    }


def format_summary(agg: dict[str, Any]) -> str:
    if not agg.get("count"):
        return "  (no headlines scored)"
    n = agg["count"]
    return "\n".join([
        f"  Headlines scored:   {n}",
        f"  Positive:           {agg['positive']:>3}  ({agg['positive'] / n * 100:>5.1f}%)",
        f"  Neutral:            {agg['neutral']:>3}  ({agg['neutral'] / n * 100:>5.1f}%)",
        f"  Negative:           {agg['negative']:>3}  ({agg['negative'] / n * 100:>5.1f}%)",
        f"  Net score (-1..+1): {agg['net_score']:>+.3f}",
        f"  Majority label:     {agg['label_majority']}",
    ])


# --------------------------- CLI ------------------------------------------- #

def _read_inputs(args) -> list[str]:
    texts: list[str] = []
    if args.text:
        texts.extend(args.text)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            texts.extend(line.strip() for line in f if line.strip())
    if not texts and not sys.stdin.isatty():
        texts.extend(line.strip() for line in sys.stdin if line.strip())
    return texts


def main() -> None:
    p = argparse.ArgumentParser(
        description="Crypto/financial text sentiment via FinBERT (default) or FinGPT LoRA.",
    )
    p.add_argument("--text", action="append", help="Inline text. Can be repeated.")
    p.add_argument("--file", help="File with one headline per line.")
    p.add_argument("--backend", choices=["finbert", "fingpt"], default="finbert")
    p.add_argument("--model", help="HuggingFace model id (FinBERT backend).")
    p.add_argument("--base-model", help="Base model for FinGPT backend.")
    p.add_argument("--lora-repo", help="LoRA adapter repo for FinGPT backend.")
    p.add_argument("--per-text", action="store_true", help="Print every text's score, not just the summary.")
    p.add_argument("--json", action="store_true", help="JSON output.")
    args = p.parse_args()

    texts = _read_inputs(args)
    if not texts:
        p.error("No input texts. Use --text, --file, or pipe stdin.")

    print(
        f"Scoring {len(texts)} text(s) with backend='{args.backend}'...",
        file=sys.stderr,
    )
    results = score_texts(
        texts,
        backend=args.backend,
        model_name=args.model,
        base_model=args.base_model,
        lora_repo=args.lora_repo,
    )
    agg = aggregate(results)

    if args.json:
        print(json.dumps({"results": results, "summary": agg}, indent=2))
        return

    if args.per_text:
        print()
        for r in results:
            preview = r["text"][:70] + ("..." if len(r["text"]) > 70 else "")
            print(f"  [{r['label']:>8}  {r['score']:.2f}]  {preview}")

    bar = "=" * 64
    print()
    print(bar)
    print("  SENTIMENT SUMMARY  (descriptive, NOT advice)")
    print(bar)
    print(format_summary(agg))
    print(bar)


if __name__ == "__main__":
    main()
