#!/usr/bin/env python3
"""Small ambient-restricted scout on non-favourable recorded-free CICYs."""

from __future__ import annotations

import argparse
from collections import Counter
from itertools import product
import json
import random
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_nonfavourable_free_capability_audit import (  # noqa: E402
    RAW,
    free_symmetry_options,
)
from string_theory.cicy import (  # noqa: E402
    ambient_dimensions,
    bundle_c1,
    bundle_c2,
    bundle_index,
    sorted_matrix_key,
    triple_intersections,
    wedge2_index,
)
from string_theory.cicy_symmetry import (  # noqa: E402
    line_bundle_sum_invariant_under_row_permutation,
)
from string_theory.cicylist import (  # noqa: E402
    parse_cicy_metadata,
    parse_integer_list_rule,
    split_top_level_entries,
)
from string_theory.novelty import build_dataset_keys, novelty_record  # noqa: E402
from string_theory.slope import find_slope_zero, intersection_tensor  # noqa: E402
from verify_candidate_novelty import gut_entries, sms_entries  # noqa: E402
from verify_family_candidate import cohomology_and_spectrum  # noqa: E402


def row_patterns(bound: int, summand_count: int = 5) -> list[tuple[int, ...]]:
    return [
        row
        for row in product(range(-bound, bound + 1), repeat=summand_count)
        if sum(row) == 0
    ]


def random_c1_zero_matrix(
    *, rng: random.Random, patterns: list[tuple[int, ...]], rows: int
) -> list[list[int]]:
    return [list(rng.choice(patterns)) for _ in range(rows)]


def novelty_context() -> dict[str, Any]:
    gut, gut_confs = gut_entries()
    sms = sms_entries()
    combined = gut + sms
    return {
        "key_sets": {
            "GUTall": build_dataset_keys(gut, gut_confs),
            "sms202": build_dataset_keys(sms, None),
            "combined": build_dataset_keys(combined, gut_confs),
        }
    }


def load_cicy_entries_by_num() -> dict[int, tuple[dict[str, Any], str]]:
    entries = split_top_level_entries((RAW / "cicylist.m").read_text(encoding="utf-8"))
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    return {meta["Num"]: (meta, entry) for meta, entry in zip(metadata, entries)}


def compatible_free_options(
    matrix: list[list[int]], options: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    compatible = []
    for option in options:
        if not option["ambient_row_permutations_inferred"]:
            continue
        if all(
            line_bundle_sum_invariant_under_row_permutation(matrix, tuple(perm))
            for perm in option["generator_ambient_row_permutations"]
        ):
            compatible.append(
                {
                    "option_index": option["option_index"],
                    "quotient_order": option["quotient_order"],
                    "quotient_group_structure": option["quotient_group_structure"],
                    "all_generators_ambient_row_trivial": option[
                        "all_generators_ambient_row_trivial"
                    ],
                }
            )
    return compatible


def target_priority(record: dict[str, Any]) -> tuple[Any, ...]:
    spectrum = record.get("cohomology_and_spectrum", {}).get(
        "su5_upstairs_spectrum", {}
    )
    return (
        0 if record.get("passes_upstairs_spectrum_gate") else 1,
        spectrum.get("upstairs_anti_10", 999),
        spectrum.get("upstairs_5", 999),
        record["trivial_summand_count"],
        record["max_entry_abs"],
        sum(record["anomaly"]),
        record["sample_index"],
    )


def run_search(
    *,
    target_count: int,
    samples: int,
    bound: int,
    slope_limit_per_target: int,
    seed: int,
    progress: bool,
) -> dict[str, Any]:
    audit = json.loads(
        (REPORTS / "nonfavourable_free_capability_audit.json").read_text(
            encoding="utf-8"
        )
    )
    selected_nums = [
        item["num"]
        for item in audit["selected_ambient_restricted_scout_targets"][:target_count]
    ]
    entries_by_num = load_cicy_entries_by_num()
    patterns = row_patterns(bound)
    novelty = novelty_context()

    target_reports = []
    all_slope_records = []
    for target_num in selected_nums:
        meta, entry = entries_by_num[target_num]
        conf = parse_integer_list_rule(entry, "Conf")
        c2_tx = parse_integer_list_rule(entry, "C2")
        dimensions = list(ambient_dimensions(conf))
        options = free_symmetry_options(entry, [dim + 1 for dim in dimensions])
        min_order = min(
            option["quotient_order"]
            for option in options
            if option["quotient_order"] is not None
        )
        expected_index = -3 * min_order
        intersections = triple_intersections(conf)
        tensor = intersection_tensor(intersections, len(conf))
        rng = random.Random(seed + target_num)
        seen = set()
        first_failure = Counter()
        algebraic_records = []
        index_pair_counts = Counter()

        for sample_index in range(1, samples + 1):
            matrix = random_c1_zero_matrix(
                rng=rng, patterns=patterns, rows=len(conf)
            )
            key = sorted_matrix_key(matrix)
            if key in seen:
                first_failure["duplicate_key"] += 1
                continue
            seen.add(key)
            try:
                index_v = bundle_index(matrix, intersections, c2_tx)
                index_wedge2_v = wedge2_index(matrix, intersections, c2_tx)
                c2_v = bundle_c2(matrix, intersections)
            except ValueError:
                first_failure["nonintegral_topology"] += 1
                continue
            index_pair_counts[(index_v, index_wedge2_v)] += 1
            if index_v != expected_index or index_wedge2_v != expected_index:
                first_failure["ambient_restricted_index_target"] += 1
                continue
            anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
            if not all(value >= 0 for value in anomaly):
                first_failure["ambient_restricted_anomaly_effective"] += 1
                continue
            compatible_options = compatible_free_options(matrix, options)
            if not compatible_options:
                first_failure["raw_ambient_row_symmetry_incompatibility"] += 1
                continue
            algebraic_records.append(
                {
                    "sample_index": sample_index,
                    "cicy": target_num,
                    "matrix": matrix,
                    "c1": bundle_c1(matrix),
                    "ambient_restricted_index_v": index_v,
                    "ambient_restricted_index_wedge2_v": index_wedge2_v,
                    "expected_index_from_min_free_order": expected_index,
                    "min_recorded_free_quotient_order": min_order,
                    "c2_v": c2_v,
                    "anomaly": anomaly,
                    "compatible_free_options": compatible_options[:8],
                    "trivial_summand_count": sum(
                        list(column) == [0] * len(conf) for column in zip(*matrix)
                    ),
                    "max_entry_abs": max(abs(value) for row in matrix for value in row),
                }
            )
            if progress and len(algebraic_records) <= 5:
                print(
                    f"ambient algebraic target={target_num} sample={sample_index} "
                    f"index={index_v}",
                    flush=True,
                )

        algebraic_records.sort(
            key=lambda record: (
                record["trivial_summand_count"],
                record["max_entry_abs"],
                sum(record["anomaly"]),
            )
        )
        slope_records = []
        cicy_for_cohomology = {
            "Num": target_num,
            "H11": len(conf),
            "Conf": conf,
            "C2": c2_tx,
        }
        for rank, record in enumerate(
            algebraic_records[:slope_limit_per_target], start=1
        ):
            slope = find_slope_zero(
                record["matrix"],
                tensor,
                tolerance=1e-7,
                restarts=12,
                max_iterations=1800,
                seed=seed + target_num * 1000 + rank,
            )
            slope_record = {
                **record,
                "slope_rank": rank,
                "slope_search": slope.as_dict(),
                "passes_ambient_restricted_slope_gate": slope.feasible,
                "novelty": {
                    name: novelty_record(
                        cicy_num=target_num,
                        symmetry_order=min_order,
                        matrix=record["matrix"],
                        conf=conf,
                        dataset_keys=keys,
                    )
                    for name, keys in novelty["key_sets"].items()
                },
            }
            if slope.feasible:
                cohomology = cohomology_and_spectrum(
                    cicy_for_cohomology, min_order, record["matrix"]
                )
                spectrum = cohomology["su5_upstairs_spectrum"]
                slope_record.update(
                    {
                        "cohomology_and_spectrum": cohomology,
                        "passes_upstairs_spectrum_gate": all(
                            spectrum["checks"].values()
                        ),
                    }
                )
            slope_records.append(slope_record)
            all_slope_records.append(slope_record)

        slope_records.sort(key=target_priority)
        target_reports.append(
            {
                "target": {
                    "num": target_num,
                    "h11": meta["H11"],
                    "num_projective_factors": meta["NumPs"],
                    "rank_defect": meta["H11"] - meta["NumPs"],
                    "free_symmetry_option_count": meta["FreeSymmetryOptionCount"],
                    "min_recorded_free_quotient_order": min_order,
                    "ambient_restricted_expected_index": expected_index,
                },
                "samples": samples,
                "unique_matrix_count": len(seen),
                "row_pattern_count": len(patterns),
                "first_failure_counts": dict(first_failure),
                "index_pair_counts_top20": [
                    {
                        "index_v": key[0],
                        "index_wedge2_v": key[1],
                        "count": value,
                    }
                    for key, value in index_pair_counts.most_common(20)
                ],
                "algebraic_survivor_count": len(algebraic_records),
                "slope_checked_count": len(slope_records),
                "slope_feasible_count": sum(
                    1
                    for record in slope_records
                    if record["passes_ambient_restricted_slope_gate"]
                ),
                "spectrum_pass_count": sum(
                    1
                    for record in slope_records
                    if record.get("passes_upstairs_spectrum_gate")
                ),
                "best_algebraic_records": algebraic_records[:20],
                "slope_checked_records": slope_records,
            }
        )

    spectrum_records = [
        record
        for record in all_slope_records
        if record.get("passes_upstairs_spectrum_gate")
    ]
    spectrum_records.sort(key=target_priority)
    return {
        "scope": "small ambient-restricted scout on selected non-favourable recorded-free CICYs",
        "search": {
            "target_nums": selected_nums,
            "samples_per_target": samples,
            "bound": bound,
            "seed": seed,
            "slope_limit_per_target": slope_limit_per_target,
            "row_pattern_count": len(patterns),
            "algebraic_survivor_count": sum(
                item["algebraic_survivor_count"] for item in target_reports
            ),
            "slope_checked_count": sum(
                item["slope_checked_count"] for item in target_reports
            ),
            "slope_feasible_count": sum(
                item["slope_feasible_count"] for item in target_reports
            ),
            "spectrum_pass_count": len(spectrum_records),
        },
        "target_reports": target_reports,
        "best_spectrum_records": spectrum_records[:10],
        "interpretation": {
            "not_a_full_nonfavourable_certificate": True,
            "why": "The search uses ambient-restricted divisor charges and ambient C2/intersection/Kahler data only; missing full Picard-basis geometry blocks a non-favourable line-bundle certificate.",
            "raw_symmetry_check_scope": "topological invariance under inferred ambient row permutations for recorded free options",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-count", type=int, default=3)
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--bound", type=int, default=1)
    parser.add_argument("--slope-limit-per-target", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260603)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "nonfavourable_ambient_restricted_scout.json"),
    )
    args = parser.parse_args()

    result = run_search(
        target_count=args.target_count,
        samples=args.samples,
        bound=args.bound,
        slope_limit_per_target=args.slope_limit_per_target,
        seed=args.seed,
        progress=args.progress,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    search = result["search"]
    print(f"target_nums={search['target_nums']}")
    print(f"algebraic_survivor_count={search['algebraic_survivor_count']}")
    print(f"slope_checked_count={search['slope_checked_count']}")
    print(f"slope_feasible_count={search['slope_feasible_count']}")
    print(f"spectrum_pass_count={search['spectrum_pass_count']}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
