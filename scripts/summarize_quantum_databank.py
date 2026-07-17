#!/usr/bin/env python3
"""Summarize local quantum hardware run databank and rank efficient pathways.

Example:
  cd backend && source .venv/bin/activate
  python ../scripts/summarize_quantum_databank.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from services.quantum.databank import databank_path, summarize_hardware_runs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize local quantum hardware run databank"
    )
    parser.add_argument(
        "--databank",
        default=None,
        help="Path to hardware_runs.jsonl (default: repo databank path)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top pathways to print",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional output file for full summary JSON",
    )
    args = parser.parse_args()

    path = Path(args.databank).expanduser().resolve() if args.databank else databank_path()
    summary = summarize_hardware_runs(top=args.top, path=path)
    leaderboard = summary["leaderboard"]

    if summary["record_count"] == 0:
        print(f"No quantum_hardware_run records found in {path}")
        return 0

    print(f"Loaded {summary['record_count']} hardware run records from {path}")
    print("\nTop pathways (lower efficiency_score is better):")
    for i, row in enumerate(leaderboard, start=1):
        print(
            f"{i:2}. runs={row['runs']:3}  score={row['avg_efficiency_score']:.6f}  "
            f"abs_err={row['avg_abs_error_vs_exact']:.6f}  stderr={row['avg_standard_error']:.6f}  "
            f"shots={row['avg_shots']:.1f}  iters={row['avg_iterations']:.2f}  "
            f"conv={100.0 * row['converged_rate']:.1f}%  pathway={row['pathway']}"
        )

    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nWrote summary JSON: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
