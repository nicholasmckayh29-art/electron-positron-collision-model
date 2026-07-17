#!/usr/bin/env python3
"""Run a local verification matrix: resonances × shot counts.

Example:
  cd backend && source .venv/bin/activate
  python ../scripts/run_verification_calibration.py --csv ../path/to/dielectron.csv

With IBM hardware (requires .env):
  USE_REAL_BACKEND=true python ../scripts/run_verification_calibration.py --csv data.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv

load_dotenv(BACKEND.parent / ".env")
load_dotenv(BACKEND / ".env")

from services.analysis import load_csv_data  # noqa: E402
from services.quantum.pipeline import SnapshotVerificationPipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Verification calibration matrix")
    parser.add_argument("--csv", required=True, help="Dielectron CSV path")
    parser.add_argument(
        "--particles",
        default="jpsi,z_boson",
        help="Comma-separated resonance ids (or auto)",
    )
    parser.add_argument(
        "--shots",
        default="512,1024,4096",
        help="Comma-separated shot counts",
    )
    parser.add_argument("--json-out", default=None, help="Write results JSON here")
    args = parser.parse_args()

    data_set = load_csv_data(str(Path(args.csv).resolve()))
    if not data_set:
        print("No rows loaded from CSV.", file=sys.stderr)
        return 1

    particles = [p.strip() for p in args.particles.split(",") if p.strip()]
    shot_list = [int(s.strip()) for s in args.shots.split(",") if s.strip()]

    pipeline = SnapshotVerificationPipeline()
    rows = []

    for particle in particles:
        for shots in shot_list:
            result = pipeline.run(data_set, shots=shots, particle_name=particle)
            payload = result.to_job_payload()
            row = {
                "particle": particle,
                "shots": shots,
                "backend": payload["backend"],
                "estimate": payload["estimate"],
                "standard_error": payload["standard_error"],
                "exact": payload["exact_classical_probability"],
                "binned": payload["binned_classical_probability"],
                "verification": payload["verification"],
            }
            rows.append(row)
            print(
                f"{particle:12} shots={shots:5}  q={row['estimate']:.4f}±{row['standard_error']:.4f}  "
                f"exact={row['exact']:.4f}  binned={row['binned']:.4f}  "
                f"Δq-exact={row['verification']['quantum_vs_exact']:+.4f}"
            )

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Wrote {args.json_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
