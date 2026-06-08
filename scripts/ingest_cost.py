"""Report ingestion cost from the SQLite ledger. Usage: ingest_cost.py [--by repo|file|snippet]."""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.db import Database

LABEL = {"repo": "repo", "file": "file_path", "snippet": "snippet_name"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--by", choices=["repo", "file", "snippet"], default="repo")
    args = parser.parse_args()

    db = Database(os.environ.get("DB_PATH", "data/prove.db"))
    rows = db.ingest_cost_rollup(args.by)
    if not rows:
        print("No ingestion costs recorded yet.")
        return

    name_keys = ["repo", "file_path", "snippet_name"][: ["repo", "file", "snippet"].index(args.by) + 1]
    width = max(len(" / ".join(str(r[k]) for k in name_keys)) for r in rows)
    print(f"{'name':<{width}}  {'cost':>10}  {'in_tok':>10}  {'out_tok':>9}  rows")
    total = 0.0
    for r in rows:
        name = " / ".join(str(r[k]) for k in name_keys)
        total += r["cost_usd"]
        print(f"{name:<{width}}  ${r['cost_usd']:>8.4f}  {r['input_tokens']:>10,}  "
              f"{r['output_tokens']:>9,}  {r['rows']}")
    print(f"\nTOTAL  ${total:.4f}")


if __name__ == "__main__":
    main()
