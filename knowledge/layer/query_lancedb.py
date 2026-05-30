#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import lancedb
import torch
from transformers import AutoModel, AutoTokenizer


MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
TABLE_NAME = "library_chunks"


class QueryEmbedder:
    def __init__(self, cache_dir: Path) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            cache_dir=str(cache_dir),
        )
        self.model = AutoModel.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            cache_dir=str(cache_dir),
        ).to(self.device)
        self.model.eval()

    def encode(self, text: str) -> list[float]:
        encoded = self.tokenizer(
            [f"search_query: {text}"],
            padding=True,
            truncation=True,
            max_length=1024,
            return_tensors="pt",
        ).to(self.device)
        with torch.no_grad():
            output = self.model(**encoded)
            hidden = output.last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return pooled[0].cpu().tolist()


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the HVE LanceDB sample index.")
    parser.add_argument("--root", required=True, help="Knowledge-layer root path")
    parser.add_argument("--query", required=True, help="Semantic query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of matches to return")
    args = parser.parse_args()

    root = Path(args.root)
    embedder = QueryEmbedder(root / "state" / "model-cache")
    db = lancedb.connect(str(root / "index" / "lancedb"))
    table = db.open_table(TABLE_NAME)
    results = table.search(embedder.encode(args.query)).limit(args.top_k).to_list()

    print(f"PASS query={args.query!r} matches={len(results)}")
    for row in results:
        print("---")
        print(f"book: {row.get('book')}")
        print(f"author: {row.get('author')}")
        print(f"chapter: {row.get('chapter')}")
        print(f"pages: {row.get('page_start')}-{row.get('page_end')}")
        print(f"source: {row.get('source_path')}")
        print(f"text: {row.get('text', '')[:300]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
