#!/usr/bin/env python3
"""Pairwise exact-kappa local deformations through the CICY 7484 `K_even` point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from string_theory.characters import cicy7484_actual_wedge2_z2xz2_character_certificate  # noqa: E402
from string_theory.cicy import (  # noqa: E402
    bundle_c1,
    bundle_c2,
    bundle_index,
    sorted_matrix_key,
    triple_intersections,
    wedge2_index,
)
from string_theory.cicy_symmetry import cicy_7484_topological_equivariance_report  # noqa: E402
from string_theory.cohomology import trivial_summand_indices  # noqa: E402
from string_theory.symbolic_slope import cicy_7484_kahler_ray_for_positive_kappa  # noqa: E402

from search_cicy7484_even_global_candidates import novelty_for_matrix  # noqa: E402
from search_cicy7484_hyperplane_candidates import load_cicy_7484, novelty_key_sets  # noqa: E402
from verify_family_candidate import BASE_SYMMETRY_ORDER, cohomology_and_spectrum  # noqa: E402


REPORTS = ROOT / "reports"
RAW = ROOT / "data" / "raw"

BASE_MATRIX = [[-3, -2, 1, 2, 2], [1, -1, -2, 1, 1], [0, 1, 1, -1, -1]]
KAPPA = [1, 3, 5]


def add_pair_delta(
    matrix: list[list[int]],
    first_col: int,
    second_col: int,
    delta: tuple[int, int, int],
    n: int,
) -> list[list[int]]:
    out = [row[:] for row in matrix]
    for row, value in enumerate(delta):
        out[row][first_col] += n * value
        out[row][second_col] -= n * value
    return out


def candidate_deltas(bound: int) -> list[tuple[int, int, int]]:
    p, q, r = KAPPA
    return [
        (x, y, z)
        for x in range(-bound, bound + 1)
        for y in range(-bound, bound + 1)
        for z in range(-bound, bound + 1)
        if (x, y, z) != (0, 0, 0)
        and (x + y + z) % 2 == 0
        and p * x + q * y + r * z == 0
    ]


def actual_pair(record: dict) -> list[int] | None:
    certificate = record["actual_wedge2_character_certificate"]
    return certificate.get("per_character_pair") or certificate.get(
        "best_per_character_pair"
    )


def verify(delta_bound: int, n_min: int, n_max: int, progress: bool = False) -> dict:
    cicy = load_cicy_7484()
    intersections = triple_intersections(cicy["Conf"])
    novelty_context = novelty_key_sets()
    expected_index = -3 * BASE_SYMMETRY_ORDER
    kahler = cicy_7484_kahler_ray_for_positive_kappa(KAPPA)
    if kahler is None:
        raise ValueError(f"expected positive CICY 7484 kappa ray for {KAPPA}")

    records = []
    seen_keys = set()
    algebraic_survivor_count = 0
    spectrum_lift_count = 0
    deltas = candidate_deltas(delta_bound)
    for first_col in range(5):
        for second_col in range(first_col + 1, 5):
            for delta in deltas:
                direction = [[0 for _ in range(5)] for _ in range(3)]
                for row, value in enumerate(delta):
                    direction[row][first_col] = value
                    direction[row][second_col] = -value
                family_hard_ns = []
                for n in range(n_min, n_max + 1):
                    if n == 0:
                        continue
                    matrix = add_pair_delta(BASE_MATRIX, first_col, second_col, delta, n)
                    key = sorted_matrix_key(matrix)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    try:
                        index_v = bundle_index(matrix, intersections, cicy["C2"])
                        index_wedge2_v = wedge2_index(matrix, intersections, cicy["C2"])
                        c2_v = bundle_c2(matrix, intersections)
                    except ValueError:
                        continue
                    anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
                    if bundle_c1(matrix) != [0, 0, 0]:
                        continue
                    if index_v != expected_index or index_wedge2_v != expected_index:
                        continue
                    if not all(value >= 0 for value in anomaly):
                        continue
                    algebraic_survivor_count += 1
                    cohomology = cohomology_and_spectrum(
                        cicy, BASE_SYMMETRY_ORDER, matrix
                    )
                    spectrum = cohomology["su5_upstairs_spectrum"]
                    if not all(spectrum["checks"].values()):
                        continue
                    equivariance = cicy_7484_topological_equivariance_report(
                        RAW / "cicylist.m", matrix
                    )
                    if not equivariance["equivariant_line_bundle_sum_lift_exists"]:
                        continue
                    actual_wedge2 = cicy7484_actual_wedge2_z2xz2_character_certificate(
                        matrix, cicy["Conf"]
                    )
                    if not actual_wedge2["character_computed"]:
                        continue
                    novelty = novelty_for_matrix(matrix, cicy["Conf"], novelty_context)
                    record = {
                        "n": n,
                        "moved_columns": [first_col, second_col],
                        "delta": list(delta),
                        "direction": direction,
                        "matrix": matrix,
                        "c1": bundle_c1(matrix),
                        "summand_total_degrees": [sum(col) for col in zip(*matrix)],
                        "trivial_summand_indices": trivial_summand_indices(matrix),
                        "trivial_summand_count": len(trivial_summand_indices(matrix)),
                        "index_v": index_v,
                        "index_wedge2_v": index_wedge2_v,
                        "anomaly": anomaly,
                        "exact_slope_polystability": {
                            "scope": "pairwise local deformation in exact CICY 7484 kappa plane",
                            **kahler,
                            "line_bundle_summands_stable": True,
                            "all_summand_slopes_zero_on_exact_interior_ray": True,
                            "direct_sum_polystable_for_charge_matrix": True,
                        },
                        **cohomology,
                        "raw_symmetry_diagnostic": equivariance,
                        "actual_wedge2_character_certificate": actual_wedge2,
                        "novelty": novelty,
                    }
                    family_hard_ns.append(n)
                    spectrum_lift_count += 1
                    records.append(record)
                    if progress:
                        print(
                            f"record={len(records)} cols={[first_col, second_col]} "
                            f"delta={delta} n={n} trivial={record['trivial_summand_count']} "
                            f"pair={actual_pair(record)}",
                            flush=True,
                        )

    records.sort(
        key=lambda record: (
            record["trivial_summand_count"] > 0,
            actual_pair(record)[1] if actual_pair(record) else 99,
            actual_pair(record)[0] if actual_pair(record) else 99,
            max(abs(value) for row in record["matrix"] for value in row),
        )
    )
    nontrivial_records = [
        record for record in records if record["trivial_summand_count"] == 0
    ]
    zero_allowed_records = [
        record for record in records if record["trivial_summand_count"] > 0
    ]
    return {
        "search": {
            "cicy": 7484,
            "symmetry_order": BASE_SYMMETRY_ORDER,
            "base_matrix": BASE_MATRIX,
            "kappa_vector": KAPPA,
            "delta_bound": delta_bound,
            "n_range": [n_min, n_max],
            "candidate_delta_count": len(deltas),
            "unique_matrix_count": len(seen_keys),
            "algebraic_survivor_count": algebraic_survivor_count,
            "spectrum_lift_character_count": spectrum_lift_count,
            "nontrivial_summand_count": len(nontrivial_records),
            "trivial_summand_count": len(zero_allowed_records),
            "best_nontrivial_actual_pair": (
                actual_pair(nontrivial_records[0]) if nontrivial_records else None
            ),
            "best_zero_allowed_actual_pair": (
                min(
                    (actual_pair(record) for record in zero_allowed_records),
                    key=lambda pair: (pair[1], pair[0]),
                )
                if zero_allowed_records
                else None
            ),
            "ansatz": (
                "move two columns by +/- delta with delta in the exact "
                "kappa=(1,3,5) plane and even total degree"
            ),
        },
        "best_nontrivial_candidate": (
            nontrivial_records[0] if nontrivial_records else None
        ),
        "best_zero_allowed_candidate": (
            min(
                zero_allowed_records,
                key=lambda record: (
                    actual_pair(record)[1],
                    actual_pair(record)[0],
                    max(abs(value) for row in record["matrix"] for value in row),
                ),
            )
            if zero_allowed_records
            else None
        ),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delta-bound", type=int, default=6)
    parser.add_argument("--n-min", type=int, default=-5)
    parser.add_argument("--n-max", type=int, default=5)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy7484_pair_deformations_delta6_n5.json"),
    )
    args = parser.parse_args()

    result = verify(args.delta_bound, args.n_min, args.n_max, progress=args.progress)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"candidate_delta_count={result['search']['candidate_delta_count']}")
    print(f"unique_matrix_count={result['search']['unique_matrix_count']}")
    print(f"algebraic_survivor_count={result['search']['algebraic_survivor_count']}")
    print(f"spectrum_lift_character_count={result['search']['spectrum_lift_character_count']}")
    print(f"best_nontrivial_actual_pair={result['search']['best_nontrivial_actual_pair']}")
    print(f"best_zero_allowed_actual_pair={result['search']['best_zero_allowed_actual_pair']}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
