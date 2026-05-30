#!/usr/bin/env python3
"""
FinBERT Sentiment Tool — Hermes CFO
Uses ProsusAI/finbert to classify financial text as positive/negative/neutral.

Usage:
    python3 finbert_sentiment.py "Bitcoin surges past $100k on ETF approval news"
    echo "BTC drops 8% amid regulatory crackdown" | python3 finbert_sentiment.py
    python3 finbert_sentiment.py --batch headlines.txt

Output (JSON):
    {"text": "...", "label": "positive", "score": 0.97, "positive": 0.97, "negative": 0.02, "neutral": 0.01}

Exit codes:
    0 = success
    1 = error
"""

import sys
import json
import os
import argparse
import re
from pathlib import Path

# Use local model cache — avoids root-owned ~/.cache/huggingface
HF_HOME = Path(__file__).parent / "models"
os.environ.setdefault("HF_HOME", str(HF_HOME))
os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")

MODEL_ID = "ProsusAI/finbert"
MAX_LENGTH = 512  # BERT hard limit


def load_model():
    """Load tokenizer and model. First call downloads weights if missing."""
    from transformers import BertTokenizer, BertForSequenceClassification
    import torch

    tokenizer = BertTokenizer.from_pretrained(MODEL_ID)
    model = BertForSequenceClassification.from_pretrained(MODEL_ID)
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    return tokenizer, model, device


def score(text: str, tokenizer, model, device) -> dict:
    """Run inference on a single text string. Returns scored dict."""
    import torch
    import torch.nn.functional as F

    text = re.sub(r"\s+", " ", text).strip()
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_LENGTH,
        padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=-1).squeeze().cpu().tolist()

    # model.config.id2label: {0: 'positive', 1: 'negative', 2: 'neutral'}
    label_map = model.config.id2label
    scores = {label_map[i]: round(probs[i], 4) for i in range(len(probs))}
    top_label = max(scores, key=scores.get)

    return {
        "text": text,
        "label": top_label,
        "score": scores[top_label],
        **scores,
    }


def main():
    parser = argparse.ArgumentParser(
        description="FinBERT financial sentiment scorer for Hermes CFO"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Headline or text to score (or pipe via stdin)",
    )
    parser.add_argument(
        "--batch",
        metavar="FILE",
        help="Score each line in FILE (one headline per line)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress model load messages",
    )
    args = parser.parse_args()

    if args.quiet:
        os.environ["TRANSFORMERS_VERBOSITY"] = "error"
        import logging
        logging.getLogger("transformers").setLevel(logging.ERROR)

    try:
        tokenizer, model, device = load_model()
    except Exception as e:
        print(json.dumps({"error": f"Model load failed: {e}"}), file=sys.stderr)
        sys.exit(1)

    if args.batch:
        path = Path(args.batch)
        if not path.exists():
            print(json.dumps({"error": f"File not found: {args.batch}"}), file=sys.stderr)
            sys.exit(1)
        lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
        results = [score(line, tokenizer, model, device) for line in lines]
        print(json.dumps(results, indent=2))

    elif not sys.stdin.isatty():
        # Piped input
        text = sys.stdin.read().strip()
        if text:
            print(json.dumps(score(text, tokenizer, model, device), indent=2))

    elif args.text:
        print(json.dumps(score(args.text, tokenizer, model, device), indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
