#!/usr/bin/env python3
"""Numerically reproduce slope-zero feasibility for Oxford SU(5) benchmarks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import triple_intersections
from string_theory.mathematica import load_assignment, rules_to_dict
from string_theory.slope import find_slope_zero, intersection_tensor

from verify_gut_benchmarks import iter_models


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def verify(
    limit: int,
    tolerance: float,
    seed: int,
    restarts: int,
    max_iterations: int,
    retry_failures: bool,
    retry_restarts: int,
    retry_max_iterations: int,
) -> dict:
    cicy_entries = [rules_to_dict(entry) for entry in load_assignment(str(RAW / "GUTall.m"), "Cicys")]
    cicys = {entry["Num"]: entry for entry in cicy_entries}
    tensors = {
        num: intersection_tensor(triple_intersections(entry["Conf"]), entry["H11"])
        for num, entry in cicys.items()
    }
    line_bundle_sums = load_assignment(str(RAW / "GUTall.m"), "LineBundleSums")

    checked = []
    failures = []
    for index, (cicy, symmetry_order, matrix) in enumerate(iter_models(cicys, line_bundle_sums), start=1):
        if index > limit:
            break
        initial_result = find_slope_zero(
            matrix,
            tensors[cicy["Num"]],
            tolerance=tolerance,
            restarts=restarts,
            max_iterations=max_iterations,
            seed=seed + index,
        )
        result = initial_result
        retry_used = False
        if retry_failures and not initial_result.feasible:
            retry_used = True
            result = find_slope_zero(
                matrix,
                tensors[cicy["Num"]],
                tolerance=tolerance,
                restarts=retry_restarts,
                max_iterations=retry_max_iterations,
                seed=seed + 1000000 + index,
            )
        record = {
            "model_index": index,
            "cicy": cicy["Num"],
            "h11": cicy["H11"],
            "symmetry_order": symmetry_order,
            "matrix": matrix,
            "slope_search": result.as_dict(),
            "retry_used": retry_used,
        }
        if retry_used:
            record["initial_slope_search"] = initial_result.as_dict()
        checked.append(record)
        if not result.feasible:
            failures.append(record)

    retry_records = [record for record in checked if record["retry_used"]]
    return {
        "dataset": "GUTall.m",
        "checked_models": len(checked),
        "tolerance": tolerance,
        "seed": seed,
        "restarts": restarts,
        "max_iterations": max_iterations,
        "retry_failures": retry_failures,
        "retry_restarts": retry_restarts if retry_failures else None,
        "retry_max_iterations": retry_max_iterations if retry_failures else None,
        "retry_count": len(retry_records),
        "retry_resolved_count": sum(
            1 for record in retry_records if record["slope_search"]["feasible"]
        ),
        "failures": failures,
        "checked": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--tolerance", type=float, default=1e-7)
    parser.add_argument("--seed", type=int, default=20260602)
    parser.add_argument("--restarts", type=int, default=24)
    parser.add_argument("--max-iterations", type=int, default=2500)
    parser.add_argument("--retry-failures", action="store_true")
    parser.add_argument("--retry-restarts", type=int, default=96)
    parser.add_argument("--retry-max-iterations", type=int, default=8000)
    parser.add_argument("--json-out", default=str(REPORTS / "gut_slope_checks.json"))
    args = parser.parse_args()

    result = verify(
        args.limit,
        args.tolerance,
        args.seed,
        args.restarts,
        args.max_iterations,
        args.retry_failures,
        args.retry_restarts,
        args.retry_max_iterations,
    )
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    worst = max(
        (record["slope_search"]["max_normalized_slope"] for record in result["checked"]),
        default=0.0,
    )
    print(f"checked_models={result['checked_models']}")
    print(f"tolerance={result['tolerance']}")
    print(f"restarts={result['restarts']}")
    print(f"max_iterations={result['max_iterations']}")
    print(f"retry_failures={result['retry_failures']}")
    print(f"retry_count={result['retry_count']}")
    print(f"retry_resolved_count={result['retry_resolved_count']}")
    print(f"failures={len(result['failures'])}")
    print(f"worst_max_normalized_slope={worst:.6g}")
    print(f"json_out={out}")
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
