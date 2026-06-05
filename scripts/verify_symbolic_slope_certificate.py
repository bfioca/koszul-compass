#!/usr/bin/env python3
"""Write the exact slope/anomaly certificate for the CICY 7484 family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.symbolic_slope import cicy_7484_family_symbolic_gate


REPORTS = ROOT / "reports"


def verify(n_min: int, n_max: int) -> dict:
    records = [cicy_7484_family_symbolic_gate(n) for n in range(n_min, n_max + 1)]
    return {
        "candidate": {
            "cicy": 7484,
            "symmetry_order": 4,
            "family": [
                ["1-n", "-4+n", "1", "1", "1"],
                ["3-n", "n", "-1", "-1", "-1"],
                ["-1", "1", "0", "0", "0"],
            ],
        },
        "exact_statements": {
            "index_v": "-12",
            "index_wedge2_v": "-12",
            "anomaly": ["16 + 8 n", "8 + 8 n", "12 - 16 n + 8 n^2"],
            "slope_feasible_integer_condition": "n <= 1",
            "anomaly_nonnegative_integer_condition": "n >= -1",
            "slope_and_anomaly_integer_segment": [-1, 0, 1],
            "polystability_statement": (
                "Line-bundle summands are stable; the exact interior slope-zero "
                "ray therefore makes the direct sum poly-stable."
            ),
            "exact_polystable_and_anomaly_integer_segment": [-1, 0, 1],
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-min", type=int, default=-8)
    parser.add_argument("--n-max", type=int, default=8)
    parser.add_argument("--json-out", default=str(REPORTS / "symbolic_slope_7484_shift12.json"))
    args = parser.parse_args()
    result = verify(args.n_min, args.n_max)
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    segment = [
        record["n"] for record in result["records"] if record["exact_polystable_and_anomaly_pass"]
    ]
    print(f"exact_polystable_and_anomaly_segment={segment}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
