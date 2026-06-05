#!/usr/bin/env python3
"""Local two-column deformation scout around the outside-regime CICY 2544 hit."""

from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from string_theory.cicy import (
    bundle_c1,
    bundle_c2,
    bundle_index,
    sorted_matrix_key,
    triple_intersections,
    wedge2_index,
)
from string_theory.slope import find_slope_zero, intersection_tensor

from verify_family_candidate import cohomology_and_spectrum


REPORTS = ROOT / "reports"


def load_base() -> tuple[dict, list[list[int]], dict]:
    cert = json.loads((REPORTS / "outside_regime_candidate_certificate.json").read_text())
    target_pool = json.loads((REPORTS / "outside_regime_targets.json").read_text())
    cicy_num = cert["construction"]["cicy"]
    target = next(
        item
        for item in target_pool["immediate_favourable_targets"]
        if item["num"] == cicy_num
    )
    cicy = {
        "Num": cicy_num,
        "H11": target["h11"],
        "Conf": target["conf"],
        "C2": target["c2"],
    }
    return cicy, cert["construction"]["matrix"], {
        "base_candidate_label": cert["construction"]["label"],
        "base_candidate_source": cert["construction"].get("source"),
        "base_candidate_search_report": cert["construction"]["search_report"],
        "base_candidate_certificate": "reports/outside_regime_candidate_certificate.json",
    }


def add_pair_delta(
    matrix: list[list[int]], col_a: int, col_b: int, delta: tuple[int, ...]
) -> list[list[int]]:
    out = [row[:] for row in matrix]
    for row_index, value in enumerate(delta):
        out[row_index][col_a] += value
        out[row_index][col_b] -= value
    return out


def verify(*, delta_bound: int, slope_limit: int, progress: bool) -> dict:
    cicy, base_matrix, base_context = load_base()
    intersections = triple_intersections(cicy["Conf"])
    tensor = intersection_tensor(intersections, cicy["H11"])
    deltas = [
        tuple(delta)
        for delta in product(range(-delta_bound, delta_bound + 1), repeat=cicy["H11"])
        if any(value != 0 for value in delta)
    ]

    algebraic_records = []
    seen = set()
    first_failure = Counter()
    for col_a, col_b in combinations(range(5), 2):
        for delta in deltas:
            matrix = add_pair_delta(base_matrix, col_a, col_b, delta)
            key = sorted_matrix_key(matrix)
            if key in seen:
                first_failure["duplicate_key"] += 1
                continue
            seen.add(key)
            try:
                index_v = bundle_index(matrix, intersections, cicy["C2"])
                index_wedge2_v = wedge2_index(matrix, intersections, cicy["C2"])
                c2_v = bundle_c2(matrix, intersections)
            except ValueError:
                first_failure["nonintegral_topology"] += 1
                continue
            if index_v != -3 or index_wedge2_v != -3:
                first_failure["index_target"] += 1
                continue
            anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
            if not all(value >= 0 for value in anomaly):
                first_failure["anomaly_effective"] += 1
                continue
            algebraic_records.append(
                {
                    "columns": [col_a, col_b],
                    "delta": list(delta),
                    "matrix": matrix,
                    "c1": bundle_c1(matrix),
                    "index_v": index_v,
                    "index_wedge2_v": index_wedge2_v,
                    "c2_v": c2_v,
                    "anomaly": anomaly,
                    "max_entry_abs": max(abs(value) for row in matrix for value in row),
                    "delta_l1": sum(abs(value) for value in delta),
                    "delta_linf": max(abs(value) for value in delta),
                    "trivial_summand_count": sum(
                        list(column) == [0] * cicy["H11"] for column in zip(*matrix)
                    ),
                }
            )
    algebraic_records.sort(
        key=lambda record: (
            record["trivial_summand_count"],
            record["max_entry_abs"],
            record["delta_l1"],
            sum(record["anomaly"]),
        )
    )

    slope_records = []
    for rank, record in enumerate(algebraic_records[:slope_limit], start=1):
        slope = find_slope_zero(
            record["matrix"],
            tensor,
            tolerance=1e-7,
            restarts=16,
            max_iterations=2000,
            seed=2544000 + rank,
        )
        slope_record = {
            **record,
            "slope_rank": rank,
            "slope_search": slope.as_dict(),
            "passes_slope_gate": slope.feasible,
        }
        if slope.feasible:
            cohomology = cohomology_and_spectrum(cicy, 1, record["matrix"])
            spectrum = cohomology["su5_upstairs_spectrum"]
            slope_record.update(
                {
                    "cohomology_and_spectrum": cohomology,
                    "passes_upstairs_spectrum_gate": all(spectrum["checks"].values()),
                }
            )
        slope_records.append(slope_record)
        if progress:
            print(
                f"slope rank={rank}/{min(slope_limit, len(algebraic_records))} "
                f"feasible={slope.feasible}",
                flush=True,
            )

    spectrum_records = [
        record
        for record in slope_records
        if record.get("passes_upstairs_spectrum_gate")
    ]
    spectrum_records.sort(
        key=lambda record: (
            record["cohomology_and_spectrum"]["su5_upstairs_spectrum"][
                "upstairs_anti_10"
            ],
            record["cohomology_and_spectrum"]["su5_upstairs_spectrum"]["upstairs_5"],
            record["max_entry_abs"],
            record["delta_l1"],
        )
    )
    return {
        "scope": (
            "local two-column deformation scout around "
            f"{base_context['base_candidate_label']}"
        ),
        "search": {
            "cicy": cicy["Num"],
            "delta_bound": delta_bound,
            "delta_count": len(deltas),
            "column_pair_count": 10,
            "unique_matrix_count": len(seen),
            "algebraic_survivor_count": len(algebraic_records),
            "slope_checked_count": len(slope_records),
            "slope_feasible_count": sum(
                1 for record in slope_records if record["passes_slope_gate"]
            ),
            "spectrum_pass_count": len(spectrum_records),
            "first_failure_counts": dict(first_failure),
        },
        "base_context": base_context,
        "base_matrix": base_matrix,
        "best_algebraic_records": algebraic_records[:20],
        "slope_checked_records": slope_records,
        "spectrum_pass_records": spectrum_records,
        "best_spectrum_records": spectrum_records[:10],
        "interpretation": {
            "status": "local_cluster_evidence",
            "not_a_parametric_family_proof": True,
            "note": "Two-column +/-delta moves preserve c1(V)=0 by construction; this scout checks nearby hard-gate persistence but does not prove a symbolic family.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delta-bound", type=int, default=1)
    parser.add_argument("--slope-limit", type=int, default=100)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_local_deformations_delta1.json"),
    )
    args = parser.parse_args()

    result = verify(
        delta_bound=args.delta_bound,
        slope_limit=args.slope_limit,
        progress=args.progress,
    )
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    search = result["search"]
    print(f"unique_matrix_count={search['unique_matrix_count']}")
    print(f"algebraic_survivor_count={search['algebraic_survivor_count']}")
    print(f"slope_checked_count={search['slope_checked_count']}")
    print(f"slope_feasible_count={search['slope_feasible_count']}")
    print(f"spectrum_pass_count={search['spectrum_pass_count']}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
