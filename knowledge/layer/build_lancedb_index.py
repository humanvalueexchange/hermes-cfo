#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import lancedb
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from common import iter_jsonl, load_manifest, now_iso, save_manifest


MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
TABLE_NAME = "library_chunks"


class Embedder:
    def __init__(self, model_name: str, cache_dir: Path, device: str) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            cache_dir=str(cache_dir),
        )
        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            cache_dir=str(cache_dir),
        ).to(self.device)
        self.model.eval()

    def encode(self, texts: list[str], prefix: str, batch_size: int = 16) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            prepared = [f"{prefix}: {text}" for text in batch]
            encoded = self.tokenizer(
                prepared,
                padding=True,
                truncation=True,
                max_length=1024,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                output = self.model(**encoded)
                hidden = output.last_hidden_state
                mask = encoded["attention_mask"].unsqueeze(-1)
                summed = (hidden * mask).sum(dim=1)
                counts = mask.sum(dim=1).clamp(min=1)
                pooled = summed / counts
                pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            vectors.extend(pooled.cpu().numpy().astype(np.float32).tolist())
            del encoded, output, hidden, mask, summed, counts, pooled
            if self.device == "cuda":
                torch.cuda.empty_cache()
        return vectors


def resolve_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but not available")
    return device


def load_chunk_records(root: Path, chunk_files: list[Path] | None = None) -> list[dict]:
    records: list[dict] = []
    files = chunk_files or sorted((root / "processed" / "chunks").glob("*.jsonl"))
    for chunk_file in files:
        records.extend(iter_jsonl(chunk_file))
    return records


def document_ids_for_chunk_files(chunk_files: list[Path] | None) -> set[str]:
    if not chunk_files:
        return set()
    return {chunk_file.stem for chunk_file in chunk_files}


def write_records(db: lancedb.DBConnection, records: list[dict], *, overwrite: bool, document_ids: set[str]) -> None:
    if overwrite:
        db.create_table(TABLE_NAME, data=records, mode="overwrite")
        return

    if TABLE_NAME in db.table_names():
        table = db.open_table(TABLE_NAME)
        if document_ids:
            quoted = ", ".join("'" + document_id.replace("'", "''") + "'" for document_id in sorted(document_ids))
            table.delete(f"document_id IN ({quoted})")
        table.add(records, mode="append")
        return

    db.create_table(TABLE_NAME, data=records, mode="create")


def update_manifests(root: Path, document_ids: set[str]) -> None:
    manifest_dir = root / "state" / "manifests"
    for manifest_path in sorted(manifest_dir.glob("*.json")):
        if document_ids and manifest_path.stem not in document_ids:
            continue
        manifest = load_manifest(manifest_path)
        manifest["index_status"] = "completed"
        manifest["indexed_at"] = now_iso()
        manifest["index_table"] = TABLE_NAME
        save_manifest(manifest_path, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build LanceDB index for HVE library chunks.")
    parser.add_argument("--root", required=True, help="Knowledge-layer root path")
    parser.add_argument("--limit", type=int, default=0, help="Optional chunk limit")
    parser.add_argument(
        "--chunk-file",
        action="append",
        default=[],
        help="Specific chunk JSONL file to index; repeat to limit indexing to a batch",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Embedding device selection",
    )
    args = parser.parse_args()

    root = Path(args.root)
    chunk_files = [Path(value) for value in args.chunk_file]
    records = load_chunk_records(root, chunk_files or None)
    if args.limit:
        records = records[: args.limit]
    if not records:
        print(f"PASS records=0 root={root}")
        return 0

    model_cache = root / "state" / "model-cache"
    resolved_device = resolve_device(args.device)
    embedder = Embedder(MODEL_NAME, model_cache, resolved_device)
    embeddings = embedder.encode([record["text"] for record in records], "search_document")
    for record, vector in zip(records, embeddings):
        record["vector"] = vector

    db = lancedb.connect(str(root / "index" / "lancedb"))
    document_ids = document_ids_for_chunk_files(chunk_files or None)
    write_records(db, records, overwrite=not chunk_files, document_ids=document_ids)
    update_manifests(root, document_ids)

    print(
        f"PASS records={len(records)} table={TABLE_NAME} root={root} "
        f"device={resolved_device} mode={'overwrite' if not chunk_files else 'append'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
