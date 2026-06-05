#!/usr/bin/env python3
"""Obstruction-aware global bounded search on CICY 7484."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
import sympy as sp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from string_theory.cicy import (  # noqa: E402
    bundle_c1,
    bundle_c2,
    bundle_index,
    sorted_matrix_key,
    triple_intersections,
    wedge2_index,
)
from string_theory.cicy_symmetry import cicy_7484_topological_equivariance_report  # noqa: E402
from string_theory.characters import cicy7484_actual_wedge2_z2xz2_character_certificate  # noqa: E402
from string_theory.novelty import novelty_record  # noqa: E402
from string_theory.symbolic_slope import cicy_7484_kahler_ray_for_positive_kappa  # noqa: E402

from search_cicy7484_hyperplane_candidates import (  # noqa: E402
    load_cicy_7484,
    matrix_from_columns,
    novelty_key_sets,
    zero_sum_column_multisets,
)
from verify_family_candidate import BASE_SYMMETRY_ORDER, cohomology_and_spectrum  # noqa: E402


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def even_total_columns(bound: int) -> list[tuple[int, int, int]]:
    return [
        (x, y, z)
        for x in range(-bound, bound + 1)
        for y in range(-bound, bound + 1)
        for z in range(-bound, bound + 1)
        if (x, y, z) != (0, 0, 0) and (x + y + z) % 2 == 0
    ]


def fast_positive_kappa_prefilter(matrix: list[list[int]], tolerance: float = 1e-9) -> bool:
    array = np.array(matrix, dtype=float).T
    _, singular_values, vh = np.linalg.svd(array, full_matrices=True)
    if singular_values[-1] > tolerance:
        return False
    vector = vh[-1]
    return bool(np.all(vector > tolerance) or np.all(vector < -tolerance))


def primitive_positive_kappa_relation(matrix: list[list[int]]) -> list[int] | None:
    nullspace = sp.Matrix(matrix).T.nullspace()
    for vector in nullspace:
        values = [sp.Rational(value) for value in vector]
        for sign in [1, -1]:
            signed = [sign * value for value in values]
            if all(value > 0 for value in signed):
                lcm = int(sp.ilcm(*[value.q for value in signed]))
                integers = [int(value * lcm) for value in signed]
                gcd = abs(math.gcd(math.gcd(integers[0], integers[1]), integers[2]))
                return [value // gcd for value in integers]
    return None


def novelty_for_matrix(matrix: list[list[int]], conf: list[list[int]], novelty_context: dict) -> dict:
    key_sets = novelty_context["key_sets"]
    return {
        "dataset_counts": novelty_context["dataset_counts"],
        "datasets": {
            "GUTall": novelty_record(
                cicy_num=7484,
                symmetry_order=BASE_SYMMETRY_ORDER,
                matrix=matrix,
                conf=conf,
                dataset_keys=key_sets["GUTall"],
            ),
            "sms202": novelty_record(
                cicy_num=7484,
                symmetry_order=BASE_SYMMETRY_ORDER,
                matrix=matrix,
                conf=conf,
                dataset_keys=key_sets["sms202"],
            ),
            "combined": novelty_record(
                cicy_num=7484,
                symmetry_order=BASE_SYMMETRY_ORDER,
                matrix=matrix,
                conf=conf,
                dataset_keys=key_sets["combined"],
            ),
        },
    }


def verify(bound: int, progress: bool = False) -> dict:
    cicy = load_cicy_7484()
    novelty_context = novelty_key_sets()
    intersections = triple_intersections(cicy["Conf"])
    expected_index = -3 * BASE_SYMMETRY_ORDER
    columns = even_total_columns(bound)
    zero_sum_indices = zero_sum_column_multisets(columns)

    records = []
    seen_keys = set()
    positive_kappa_count = 0
    algebraic_survivor_count = 0
    for index, indices in enumerate(zero_sum_indices, start=1):
        matrix = matrix_from_columns(columns, indices)
        key = sorted_matrix_key(matrix)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        if not fast_positive_kappa_prefilter(matrix):
            continue
        positive_kappa_count += 1
        kappa = primitive_positive_kappa_relation(matrix)
        if kappa is None:
            continue
        kahler = cicy_7484_kahler_ray_for_positive_kappa(kappa)
        if kahler is None:
            continue
        try:
            index_v = bundle_index(matrix, intersections, cicy["C2"])
            index_wedge2_v = wedge2_index(matrix, intersections, cicy["C2"])
            c2_v = bundle_c2(matrix, intersections)
        except ValueError:
            continue
        anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
        if index_v != expected_index or index_wedge2_v != expected_index:
            continue
        if not all(value >= 0 for value in anomaly):
            continue
        algebraic_survivor_count += 1
        cohomology = cohomology_and_spectrum(cicy, BASE_SYMMETRY_ORDER, matrix)
        spectrum = cohomology["su5_upstairs_spectrum"]
        if not all(spectrum["checks"].values()):
            continue
        equivariance = cicy_7484_topological_equivariance_report(
            RAW / "cicylist.m", matrix
        )
        descent = cohomology["conditional_order4_descent_constraints"]
        descent["raw_symmetry_equivariant_lift_available"] = equivariance[
            "equivariant_line_bundle_sum_lift_exists"
        ]
        if "z2xz2_wilson_line_spectrum_envelope" in descent:
            descent["z2xz2_wilson_line_spectrum_envelope"][
                "applicable_to_candidate_raw_symmetry"
            ] = equivariance["equivariant_line_bundle_sum_lift_exists"]
        actual_wedge2 = cicy7484_actual_wedge2_z2xz2_character_certificate(
            matrix, cicy["Conf"]
        )
        descent["actual_z2xz2_wedge2_character_certificate"] = actual_wedge2
        descent["full_wilson_line_spectrum_proven"] = (
            equivariance["equivariant_line_bundle_sum_lift_exists"]
            and actual_wedge2["character_computed"]
            and descent["ten_sector"]["actual_h1_representation_forced_regular_multiplicity"]
            == 3
        )
        if "z2xz2_wilson_line_spectrum_envelope" in descent:
            descent["z2xz2_wilson_line_spectrum_envelope"][
                "actual_wilson_line_spectrum_proven"
            ] = descent["full_wilson_line_spectrum_proven"]
            descent["z2xz2_wilson_line_spectrum_envelope"][
                "actual_per_character_pair"
            ] = actual_wedge2.get("per_character_pair")
        records.append(
            {
                "matrix": matrix,
                "summand_total_degrees": [sum(col) for col in zip(*matrix)],
                "c1": bundle_c1(matrix),
                "index_v": index_v,
                "index_wedge2_v": index_wedge2_v,
                "anomaly": anomaly,
                "max_entry_abs": max(abs(value) for row in matrix for value in row),
                "exact_slope_polystability": {
                    "scope": "exact CICY 7484 positive-kappa ray from charge nullspace",
                    **kahler,
                    "line_bundle_summands_stable": True,
                    "all_summand_slopes_zero_on_exact_interior_ray": True,
                    "direct_sum_polystable_for_charge_matrix": True,
                },
                **cohomology,
                "raw_symmetry_diagnostic": equivariance,
                "novelty": novelty_for_matrix(matrix, cicy["Conf"], novelty_context),
                "ranking": {
                    "upstairs_anti_10": spectrum["upstairs_anti_10"],
                    "upstairs_5": spectrum["upstairs_5"],
                    "max_entry_abs": max(abs(value) for row in matrix for value in row),
                    "anomaly_sum": sum(anomaly),
                },
            }
        )
        if progress:
            print(
                f"record={len(records)} index={index}/{len(zero_sum_indices)} "
                f"spectrum={spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}",
                flush=True,
            )

    records.sort(
        key=lambda item: (
            not item["raw_symmetry_diagnostic"]["equivariant_line_bundle_sum_lift_exists"],
            item["su5_upstairs_spectrum"]["upstairs_anti_10"],
            item["su5_upstairs_spectrum"]["upstairs_5"],
            item["max_entry_abs"],
            sum(item["anomaly"]),
        )
    )
    lift_records = [
        record
        for record in records
        if record["raw_symmetry_diagnostic"]["equivariant_line_bundle_sum_lift_exists"]
    ]
    return {
        "search": {
            "cicy": 7484,
            "symmetry_order": BASE_SYMMETRY_ORDER,
            "entry_bound": bound,
            "require_even_total_degree": True,
            "ansatz": "all five even-total-degree columns in [-bound,bound]^3 with c1=0",
            "candidate_column_count": len(columns),
            "zero_sum_multiset_count": len(zero_sum_indices),
            "unique_zero_sum_multiset_count": len(seen_keys),
            "positive_kappa_prefilter_count": positive_kappa_count,
            "algebraic_survivor_count": algebraic_survivor_count,
            "spectrum_pass_count": len(records),
            "linearized_free_order_four_lift_count": len(lift_records),
        },
        "best_candidate": records[0] if records else None,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bound", type=int, default=3)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy7484_even_global_search_bound3.json"),
    )
    args = parser.parse_args()

    result = verify(args.bound, progress=args.progress)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"candidate_column_count={result['search']['candidate_column_count']}")
    print(f"zero_sum_multiset_count={result['search']['zero_sum_multiset_count']}")
    print(f"positive_kappa_prefilter_count={result['search']['positive_kappa_prefilter_count']}")
    print(f"algebraic_survivor_count={result['search']['algebraic_survivor_count']}")
    print(f"spectrum_pass_count={result['search']['spectrum_pass_count']}")
    print(f"linearized_free_order_four_lift_count={result['search']['linearized_free_order_four_lift_count']}")
    if result["best_candidate"] is not None:
        best = result["best_candidate"]
        spectrum = best["su5_upstairs_spectrum"]
        print(f"best_matrix={best['matrix']}")
        print(
            "best_spectrum="
            f"10={spectrum['upstairs_10']} anti10={spectrum['upstairs_anti_10']} "
            f"5bar/5={spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}"
        )
        print(
            "best_lift="
            f"{best['raw_symmetry_diagnostic']['equivariant_line_bundle_sum_lift_exists']}"
        )
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
