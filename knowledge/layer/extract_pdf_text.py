#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

from common import clear_failure

def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_manifests(root: Path) -> list[Path]:
    manifest_dir = root / "state" / "manifests"
    if not manifest_dir.exists():
        return []
    return sorted(manifest_dir.glob("*.json"))


def update_manifest(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def extract_text(pdf_path: Path, text_path: Path) -> tuple[bool, str | None]:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return False, "pdftotext not installed"
    text_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [pdftotext, "-layout", str(pdf_path), str(text_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stderr.strip() or "pdftotext failed"
    return True, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text from HVE library PDFs.")
    parser.add_argument("--root", required=True, help="Knowledge-layer root path")
    parser.add_argument("--limit", type=int, default=5, help="Max manifests to process")
    args = parser.parse_args()

    root = Path(args.root)
    processed = 0
    for manifest_path in load_manifests(root):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if payload.get("extraction_status") == "completed":
            continue
        pdf_path = Path(payload["source_path"])
        if not pdf_path.exists():
            payload["extraction_status"] = "failed"
            payload["extraction_error"] = "source PDF missing"
            update_manifest(manifest_path, payload)
            continue

        text_path = root / "processed" / "text" / f"{payload['document_id']}.txt"
        ok, error = extract_text(pdf_path, text_path)
        if ok:
            payload["extraction_status"] = "completed"
            payload["ingest_status"] = "extracted"
            payload["extracted_text_path"] = str(text_path)
            payload["extracted_at"] = now_iso()
            payload["extraction_error"] = None
            clear_failure(root, payload["document_id"], "extraction")
        else:
            payload["extraction_status"] = "failed"
            payload["extraction_error"] = error
        update_manifest(manifest_path, payload)
        processed += 1
        if processed >= args.limit:
            break

    print(f"PASS processed={processed} root={root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
