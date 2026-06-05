#!/usr/bin/env python3
"""Bounded hyperplane search for cleaner CICY 7484 line-bundle candidates."""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations_with_replacement
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
from string_theory.cicy_symmetry import cicy_7484_topological_equivariance_report
from string_theory.mathematica import load_assignment, rules_to_dict
from string_theory.novelty import build_dataset_keys, novelty_record
from string_theory.symbolic_slope import cicy_7484_kahler_ray_for_kappa_ratio

from verify_candidate_novelty import gut_entries, sms_entries
from verify_family_candidate import BASE_SYMMETRY_ORDER, cohomology_and_spectrum


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def candidate_columns_for_ratio(
    ratio: int, bound: int, require_even_total_degree: bool = False
) -> list[tuple[int, int, int]]:
    columns = []
    for x in range(-bound, bound + 1):
        for y in range(-bound, bound + 1):
            z_numerator = -(x + y)
            if z_numerator % ratio:
                continue
            z = z_numerator // ratio
            if -bound <= z <= bound and (x, y, z) != (0, 0, 0):
                if require_even_total_degree and (x + y + z) % 2:
                    continue
                columns.append((x, y, z))
    return sorted(set(columns))


def zero_sum_column_multisets(
    columns: list[tuple[int, int, int]], summand_count: int = 5
) -> list[tuple[int, ...]]:
    if summand_count != 5:
        raise ValueError("this optimized search currently expects five summands")

    triples: dict[tuple[int, int, int], list[tuple[int, int, int]]] = defaultdict(list)
    for triple in combinations_with_replacement(range(len(columns)), 3):
        total = tuple(sum(columns[index][row] for index in triple) for row in range(3))
        triples[total].append(triple)

    seen: set[tuple[int, ...]] = set()
    out: list[tuple[int, ...]] = []
    for pair in combinations_with_replacement(range(len(columns)), 2):
        pair_sum = tuple(sum(columns[index][row] for index in pair) for row in range(3))
        target = tuple(-value for value in pair_sum)
        for triple in triples.get(target, []):
            indices = tuple(sorted((*pair, *triple)))
            if indices not in seen:
                seen.add(indices)
                out.append(indices)
    return out


def matrix_from_columns(columns: list[tuple[int, int, int]], indices: tuple[int, ...]) -> list[list[int]]:
    return [list(row) for row in zip(*(columns[index] for index in indices))]


def load_cicy_7484() -> dict:
    cicy_entries = [rules_to_dict(entry) for entry in load_assignment(str(RAW / "GUTall.m"), "Cicys")]
    return {entry["Num"]: entry for entry in cicy_entries}[7484]


def novelty_key_sets() -> dict:
    gut, gut_confs = gut_entries()
    sms = sms_entries()
    combined = gut + sms
    return {
        "dataset_counts": {
            "GUTall": len(gut),
            "sms202": len(sms),
            "combined": len(combined),
        },
        "gut_confs": gut_confs,
        "key_sets": {
            "GUTall": build_dataset_keys(gut, gut_confs),
            "sms202": build_dataset_keys(sms, None),
            "combined": build_dataset_keys(combined, gut_confs),
        },
    }


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


def verify(
    ratios: list[int],
    bound: int,
    progress: bool = False,
    require_even_total_degree: bool = False,
) -> dict:
    cicy = load_cicy_7484()
    novelty_context = novelty_key_sets()
    intersections = triple_intersections(cicy["Conf"])
    expected_index = -3 * BASE_SYMMETRY_ORDER

    algebraic_records = []
    seen_keys = set()
    ratio_summaries = []
    for ratio in ratios:
        columns = candidate_columns_for_ratio(
            ratio, bound, require_even_total_degree=require_even_total_degree
        )
        zero_sum_indices = zero_sum_column_multisets(columns)
        ratio_survivors = 0
        for indices in zero_sum_indices:
            matrix = matrix_from_columns(columns, indices)
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
            if index_v != expected_index or index_wedge2_v != expected_index:
                continue
            if not all(value >= 0 for value in anomaly):
                continue
            ratio_survivors += 1
            algebraic_records.append(
                {
                    "kappa_ratio": ratio,
                    "matrix": matrix,
                    "c1": bundle_c1(matrix),
                    "index_v": index_v,
                    "index_wedge2_v": index_wedge2_v,
                    "anomaly": anomaly,
                    "max_entry_abs": max(abs(value) for row in matrix for value in row),
                    "exact_slope_polystability": cicy_7484_kahler_ray_for_kappa_ratio(ratio),
                }
            )
        ratio_summaries.append(
            {
                "kappa_ratio": ratio,
                "candidate_column_count": len(columns),
                "zero_sum_multiset_count": len(zero_sum_indices),
                "algebraic_survivor_count": ratio_survivors,
            }
        )
        if progress:
            print(
                "ratio_summary="
                f"m={ratio} columns={len(columns)} "
                f"zero_sum={len(zero_sum_indices)} algebraic={ratio_survivors}",
                flush=True,
            )

    records = []
    sorted_algebraic_records = sorted(
        algebraic_records,
        key=lambda item: (item["max_entry_abs"], sum(item["anomaly"]), item["kappa_ratio"]),
    )
    for index, record in enumerate(sorted_algebraic_records, start=1):
        cohomology = cohomology_and_spectrum(cicy, BASE_SYMMETRY_ORDER, record["matrix"])
        spectrum = cohomology["su5_upstairs_spectrum"]
        if not all(spectrum["checks"].values()):
            continue
        equivariance = cicy_7484_topological_equivariance_report(
            RAW / "cicylist.m", record["matrix"]
        )
        descent = cohomology["conditional_order4_descent_constraints"]
        descent["raw_symmetry_equivariant_lift_available"] = equivariance[
            "equivariant_line_bundle_sum_lift_exists"
        ]
        if "z2xz2_wilson_line_spectrum_envelope" in descent:
            descent["z2xz2_wilson_line_spectrum_envelope"][
                "applicable_to_candidate_raw_symmetry"
            ] = equivariance["equivariant_line_bundle_sum_lift_exists"]
        novelty = novelty_for_matrix(record["matrix"], cicy["Conf"], novelty_context)
        records.append(
            {
                **record,
                **cohomology,
                "raw_symmetry_diagnostic": equivariance,
                "novelty": novelty,
                "ranking": {
                    "upstairs_anti_10": spectrum["upstairs_anti_10"],
                    "upstairs_5": spectrum["upstairs_5"],
                    "max_entry_abs": record["max_entry_abs"],
                    "anomaly_sum": sum(record["anomaly"]),
                },
            }
        )
        if progress and index % 20 == 0:
            print(
                f"cohomology_progress={index}/{len(sorted_algebraic_records)} "
                f"spectrum_pass={len(records)}",
                flush=True,
            )

    records.sort(
        key=lambda item: (
            item["su5_upstairs_spectrum"]["upstairs_anti_10"],
            item["su5_upstairs_spectrum"]["upstairs_5"],
            item["max_entry_abs"],
            sum(item["anomaly"]),
        )
    )
    exact_upstairs_records = [
        record
        for record in records
        if record["su5_upstairs_spectrum"]["upstairs_anti_10"] == 0
        and record["su5_upstairs_spectrum"]["upstairs_5"] == 0
    ]
    no_anti10_records = [
        record
        for record in records
        if record["su5_upstairs_spectrum"]["upstairs_anti_10"] == 0
    ]
    linearized_lift_records = [
        record
        for record in records
        if record["raw_symmetry_diagnostic"]["equivariant_line_bundle_sum_lift_exists"]
    ]
    min_upstairs_5_no_anti10 = (
        min(record["su5_upstairs_spectrum"]["upstairs_5"] for record in no_anti10_records)
        if no_anti10_records
        else None
    )
    return {
        "search": {
            "cicy": 7484,
            "symmetry_order": BASE_SYMMETRY_ORDER,
            "entry_bound": bound,
            "require_even_total_degree": require_even_total_degree,
            "kappa_ratios": ratios,
            "hyperplane": "k1 + k2 + m k3 = 0",
            "ratio_summaries": ratio_summaries,
            "algebraic_survivor_count": len(algebraic_records),
            "spectrum_pass_count": len(records),
            "exact_upstairs_no_vectorlike_count": len(exact_upstairs_records),
            "min_upstairs_5_with_no_anti10": min_upstairs_5_no_anti10,
            "linearized_free_order_four_lift_count": len(linearized_lift_records),
            "no_anti10_and_linearized_lift_count": len(
                [
                    record
                    for record in linearized_lift_records
                    if record["su5_upstairs_spectrum"]["upstairs_anti_10"] == 0
                ]
            ),
        },
        "best_candidate": records[0] if records else None,
        "best_linearized_lift_candidate": linearized_lift_records[0]
        if linearized_lift_records
        else None,
        "exact_upstairs_no_vectorlike_records": exact_upstairs_records,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratios", nargs="*", type=int, default=[2, 4, 6, 8])
    parser.add_argument("--bound", type=int, default=6)
    parser.add_argument("--json-out", default=str(REPORTS / "hyperplane_search_7484.json"))
    parser.add_argument(
        "--require-even-total-degree",
        action="store_true",
        help=(
            "Prefilter columns to k1+k2+k3 even, the CICY 7484 Z2xZ2 "
            "projective-lift commutator condition for individual summand linearization."
        ),
    )
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    result = verify(
        args.ratios,
        args.bound,
        progress=args.progress,
        require_even_total_degree=args.require_even_total_degree,
    )
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"ratio_summaries={result['search']['ratio_summaries']}")
    print(f"algebraic_survivor_count={result['search']['algebraic_survivor_count']}")
    print(f"spectrum_pass_count={result['search']['spectrum_pass_count']}")
    print(f"exact_upstairs_no_vectorlike_count={result['search']['exact_upstairs_no_vectorlike_count']}")
    print(f"min_upstairs_5_with_no_anti10={result['search']['min_upstairs_5_with_no_anti10']}")
    print(f"linearized_free_order_four_lift_count={result['search']['linearized_free_order_four_lift_count']}")
    if result["best_candidate"] is not None:
        best = result["best_candidate"]
        spectrum = best["su5_upstairs_spectrum"]
        novelty = best["novelty"]["datasets"]["combined"]
        print(f"best_matrix={best['matrix']}")
        print(
            "best_spectrum="
            f"10/{spectrum['upstairs_anti_10']} anti10, "
            f"5bar/5={spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}"
        )
        print(
            "best_novel="
            f"{novelty['novel_under_row_and_column_permutation']}"
        )
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
