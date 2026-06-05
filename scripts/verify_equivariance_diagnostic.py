#!/usr/bin/env python3
"""Necessary ambient-row equivariance diagnostics for the CICY 7484 candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.equivariance import (
    cicy_7484_raw_symmetry_diagnostics,
    cicy_7484_symmetry_diagnostics,
)

from verify_family_candidate import BASE_MATRIX, DIRECTION, add_matrix


REPORTS = ROOT / "reports"
RAW = ROOT / "data" / "raw"


def verify(n_values: list[int]) -> dict:
    return {
        "candidate": {
            "cicy": 7484,
            "symmetry_order": 4,
            "base_matrix": BASE_MATRIX,
            "direction": DIRECTION,
        },
        "records": [
            {
                "n": n,
                "matrix": add_matrix(BASE_MATRIX, DIRECTION, n),
                "equivariance_diagnostic": cicy_7484_symmetry_diagnostics(
                    add_matrix(BASE_MATRIX, DIRECTION, n)
                ),
                "raw_symmetry_topological_diagnostic": cicy_7484_raw_symmetry_diagnostics(
                    str(RAW / "cicylist.m"),
                    add_matrix(BASE_MATRIX, DIRECTION, n),
                ),
            }
            for n in n_values
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", nargs="*", type=int, default=[-1, 0, 1])
    parser.add_argument("--json-out", default=str(REPORTS / "candidate_equivariance_7484_shift12.json"))
    args = parser.parse_args()

    result = verify(args.n)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    for record in result["records"]:
        options = record["equivariance_diagnostic"]["symmetry_options_from_cicylist"]
        status = {option["label"]: option["line_bundle_sum_invariant_up_to_columns"] for option in options}
        print(f"n={record['n']} {status}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
