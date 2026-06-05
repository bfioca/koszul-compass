#!/usr/bin/env python3
"""Reproduce algebraic benchmark checks for Oxford SU(5) line-bundle models."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import (
    bundle_c1,
    bundle_c2,
    bundle_index,
    sorted_matrix_key,
    triple_intersections,
    wedge2_index,
)
from string_theory.mathematica import load_assignment, rules_to_dict


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def iter_models(cicys: dict[int, dict], line_bundle_sums: list):
    for item in line_bundle_sums:
        if not (isinstance(item, tuple) and item[0] == "Rule"):
            raise ValueError(f"expected rule, got {item!r}")
        cicy_num, symmetry_order = item[1]
        for matrix in item[2]:
            yield cicys[cicy_num], symmetry_order, matrix


def verify(limit: int | None) -> dict:
    cicy_entries = [rules_to_dict(entry) for entry in load_assignment(str(RAW / "GUTall.m"), "Cicys")]
    cicys = {entry["Num"]: entry for entry in cicy_entries}
    intersections = {num: triple_intersections(entry["Conf"]) for num, entry in cicys.items()}
    line_bundle_sums = load_assignment(str(RAW / "GUTall.m"), "LineBundleSums")

    failures = []
    seen = set()
    count = 0
    by_cicy = Counter()
    by_symmetry = Counter()

    for cicy, symmetry_order, matrix in iter_models(cicys, line_bundle_sums):
        if limit is not None and count >= limit:
            break
        count += 1
        by_cicy[cicy["Num"]] += 1
        by_symmetry[symmetry_order] += 1

        d = intersections[cicy["Num"]]
        c1 = bundle_c1(matrix)
        c2_v = bundle_c2(matrix, d)
        anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
        ind_v = bundle_index(matrix, d, cicy["C2"])
        ind_wedge2 = wedge2_index(matrix, d, cicy["C2"])
        expected_index = -3 * symmetry_order
        novelty_key = (cicy["Num"], symmetry_order, sorted_matrix_key(matrix))

        checks = {
            "c1_zero": all(x == 0 for x in c1),
            "index_v": ind_v == expected_index,
            "index_wedge2": ind_wedge2 == expected_index,
            "anomaly_nonnegative_ambient": all(x >= 0 for x in anomaly),
            "not_duplicate_in_file": novelty_key not in seen,
        }
        seen.add(novelty_key)

        if not all(checks.values()):
            failures.append(
                {
                    "cicy": cicy["Num"],
                    "symmetry_order": symmetry_order,
                    "matrix": matrix,
                    "c1": c1,
                    "c2_v": c2_v,
                    "anomaly": anomaly,
                    "index_v": ind_v,
                    "index_wedge2": ind_wedge2,
                    "expected_index": expected_index,
                    "checks": checks,
                }
            )

    return {
        "dataset": "GUTall.m",
        "checked_models": count,
        "known_cicy_entries": len(cicys),
        "line_bundle_sum_rules": len(line_bundle_sums),
        "unique_model_keys": len(seen),
        "by_cicy": dict(by_cicy),
        "by_symmetry_order": dict(by_symmetry),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200, help="number of models to check; use 0 for all")
    parser.add_argument("--json-out", default=str(REPORTS / "gut_benchmark_checks.json"))
    args = parser.parse_args()
    limit = None if args.limit == 0 else args.limit

    result = verify(limit)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"checked_models={result['checked_models']}")
    print(f"known_cicy_entries={result['known_cicy_entries']}")
    print(f"line_bundle_sum_rules={result['line_bundle_sum_rules']}")
    print(f"unique_model_keys={result['unique_model_keys']}")
    print(f"failures={len(result['failures'])}")
    print(f"json_out={out}")
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
