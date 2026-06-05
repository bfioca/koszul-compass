#!/usr/bin/env python3
"""Deterministic algebraic scout on favourable h11=7 outside-regime targets."""

from __future__ import annotations

import argparse
from collections import Counter
from itertools import product
import json
import random
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
from string_theory.mathematica import load_assignment, rules_to_dict
from string_theory.novelty import build_dataset_keys, novelty_record
from string_theory.slope import find_slope_zero, intersection_tensor

from verify_candidate_novelty import gut_entries, sms_entries
from verify_family_candidate import cohomology_and_spectrum


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def row_patterns(bound: int, summand_count: int = 5) -> list[tuple[int, ...]]:
    return [
        row
        for row in product(range(-bound, bound + 1), repeat=summand_count)
        if sum(row) == 0
    ]


def random_c1_zero_matrix(
    *, rng: random.Random, patterns: list[tuple[int, ...]], h11: int
) -> list[list[int]]:
    return [list(rng.choice(patterns)) for _ in range(h11)]


def gutall_cicy_numbers() -> set[int]:
    cicy_entries = [
        rules_to_dict(entry) for entry in load_assignment(str(RAW / "GUTall.m"), "Cicys")
    ]
    return {entry["Num"] for entry in cicy_entries}


def novelty_context() -> dict:
    gut, gut_confs = gut_entries()
    sms = sms_entries()
    combined = gut + sms
    return {
        "dataset_counts": {
            "GUTall": len(gut),
            "sms202": len(sms),
            "combined": len(combined),
        },
        "key_sets": {
            "GUTall": build_dataset_keys(gut, gut_confs),
            "sms202": build_dataset_keys(sms, None),
            "combined": build_dataset_keys(combined, gut_confs),
        },
    }


def target_priority(record: dict) -> tuple:
    index_priority = { -3: 0, -6: 1, -9: 2, -12: 3 }.get(record["index_v"], 9)
    return (
        index_priority,
        record["trivial_summand_count"],
        record["max_entry_abs"],
        sum(record["anomaly"]),
        record["sample_index"],
    )


def verify(
    *,
    sample_count: int,
    bound: int,
    target_indices: list[int],
    slope_limit_per_target: int,
    seed: int,
    progress: bool,
) -> dict:
    target_report = json.loads((REPORTS / "outside_regime_targets.json").read_text())
    known_gutall_cicys = gutall_cicy_numbers()
    novelty = novelty_context()
    patterns = row_patterns(bound)

    target_reports = []
    all_slope_records = []
    for target in target_report["immediate_favourable_targets"]:
        cicy = {
            "Num": target["num"],
            "Conf": target["conf"],
            "C2": target["c2"],
            "H11": target["h11"],
        }
        intersections = triple_intersections(cicy["Conf"])
        tensor = intersection_tensor(intersections, cicy["H11"])
        rng = random.Random(seed + target["num"])
        seen = set()
        algebraic_records = []
        first_failure = Counter()
        index_pair_counts = Counter()

        for sample_index in range(1, sample_count + 1):
            matrix = random_c1_zero_matrix(
                rng=rng, patterns=patterns, h11=cicy["H11"]
            )
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
            index_pair_counts[(index_v, index_wedge2_v)] += 1
            if index_v not in target_indices or index_wedge2_v != index_v:
                first_failure["index_target"] += 1
                continue
            anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
            if not all(value >= 0 for value in anomaly):
                first_failure["anomaly_effective"] += 1
                continue
            trivial_count = sum(
                list(column) == [0] * cicy["H11"] for column in zip(*matrix)
            )
            algebraic_records.append(
                {
                    "sample_index": sample_index,
                    "cicy": cicy["Num"],
                    "matrix": matrix,
                    "c1": bundle_c1(matrix),
                    "index_v": index_v,
                    "index_wedge2_v": index_wedge2_v,
                    "c2_v": c2_v,
                    "anomaly": anomaly,
                    "trivial_summand_count": trivial_count,
                    "max_entry_abs": max(abs(value) for row in matrix for value in row),
                    "outside_gutall_cicy_set": cicy["Num"] not in known_gutall_cicys,
                }
            )
            if progress and len(algebraic_records) <= 5:
                print(
                    f"algebraic target={cicy['Num']} sample={sample_index} "
                    f"index={index_v}",
                    flush=True,
                )

        algebraic_records.sort(key=target_priority)
        slope_records = []
        for rank, record in enumerate(algebraic_records[:slope_limit_per_target], start=1):
            slope = find_slope_zero(
                record["matrix"],
                tensor,
                tolerance=1e-7,
                restarts=16,
                max_iterations=2000,
                seed=seed + cicy["Num"] * 1000 + rank,
            )
            slope_record = {
                **record,
                "slope_rank": rank,
                "slope_search": slope.as_dict(),
                "passes_slope_gate": slope.feasible,
                "novelty": {
                    name: novelty_record(
                        cicy_num=cicy["Num"],
                        symmetry_order=abs(record["index_v"]) // 3,
                        matrix=record["matrix"],
                        conf=cicy["Conf"],
                        dataset_keys=keys,
                    )
                    for name, keys in novelty["key_sets"].items()
                },
            }
            if slope.feasible:
                symmetry_order = abs(record["index_v"]) // 3
                cohomology = cohomology_and_spectrum(
                    cicy, symmetry_order, record["matrix"]
                )
                spectrum = cohomology["su5_upstairs_spectrum"]
                slope_record.update(
                    {
                        "cohomology_and_spectrum": cohomology,
                        "passes_upstairs_spectrum_gate": all(
                            spectrum["checks"].values()
                        ),
                        "placeholder_symmetry_order_from_index": symmetry_order,
                    }
                )
            slope_records.append(slope_record)
            all_slope_records.append(slope_record)

        target_reports.append(
            {
                "target": {
                    "num": target["num"],
                    "h11": target["h11"],
                    "h21": target["h21"],
                    "eta": target["eta"],
                    "symmetry_option_count": target["symmetry_option_count"],
                    "free_symmetry_option_count_heuristic": target[
                        "free_symmetry_option_count"
                    ],
                },
                "sample_count": sample_count,
                "unique_matrix_count": len(seen),
                "row_pattern_count": len(patterns),
                "first_failure_counts": dict(first_failure),
                "index_pair_counts_top20": [
                    {"index_v": key[0], "index_wedge2_v": key[1], "count": value}
                    for key, value in index_pair_counts.most_common(20)
                ],
                "algebraic_survivor_count": len(algebraic_records),
                "algebraic_survivor_index_counts": dict(
                    sorted(Counter(record["index_v"] for record in algebraic_records).items())
                ),
                "slope_checked_count": len(slope_records),
                "slope_feasible_count": sum(
                    1 for record in slope_records if record["passes_slope_gate"]
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

    slope_feasible_records = [
        record for record in all_slope_records if record["passes_slope_gate"]
    ]
    spectrum_records = [
        record
        for record in all_slope_records
        if record.get("passes_upstairs_spectrum_gate")
    ]
    spectrum_records.sort(
        key=lambda record: (
            record["cohomology_and_spectrum"]["su5_upstairs_spectrum"][
                "upstairs_anti_10"
            ],
            record["cohomology_and_spectrum"]["su5_upstairs_spectrum"]["upstairs_5"],
            record["slope_search"]["max_normalized_slope"],
            record["cicy"],
        )
    )
    return {
        "scope": "deterministic sampled algebraic scout on favourable h11=7 outside-GUTall targets",
        "search": {
            "bound": bound,
            "sample_count_per_target": sample_count,
            "seed": seed,
            "target_indices": target_indices,
            "slope_limit_per_target": slope_limit_per_target,
            "row_pattern_count": len(patterns),
            "row_pattern_ansatz": "sample each H11 row from all five-summand integer rows with entries in [-bound,bound] and row sum zero, guaranteeing c1(V)=0",
            "target_nums": [
                item["target"]["num"] for item in target_reports
            ],
            "algebraic_survivor_count": sum(
                item["algebraic_survivor_count"] for item in target_reports
            ),
            "slope_checked_count": len(all_slope_records),
            "slope_feasible_count": len(slope_feasible_records),
            "spectrum_pass_count": len(spectrum_records),
        },
        "target_reports": target_reports,
        "slope_feasible_records": slope_feasible_records,
        "spectrum_pass_records": spectrum_records,
        "best_spectrum_records": spectrum_records[:5],
        "interpretation": {
            "status": "scout",
            "not_a_completeness_claim": True,
            "wilson_line_status": "Known symmetry data is parsed from cicylist.m, but free action and line-bundle equivariance are not certified by this scout.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=50000)
    parser.add_argument("--bound", type=int, default=1)
    parser.add_argument("--target-index", action="append", type=int, default=None)
    parser.add_argument("--slope-limit-per-target", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260602)
    parser.add_argument("--progress", action="store_true")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_algebraic_scout_bound1_samples50000.json"),
    )
    args = parser.parse_args()

    target_indices = args.target_index or [-3, -6, -9, -12]
    result = verify(
        sample_count=args.samples,
        bound=args.bound,
        target_indices=target_indices,
        slope_limit_per_target=args.slope_limit_per_target,
        seed=args.seed,
        progress=args.progress,
    )
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    search = result["search"]
    print(f"target_nums={search['target_nums']}")
    print(f"sample_count_per_target={search['sample_count_per_target']}")
    print(f"algebraic_survivor_count={search['algebraic_survivor_count']}")
    print(f"slope_checked_count={search['slope_checked_count']}")
    print(f"slope_feasible_count={search['slope_feasible_count']}")
    print(f"spectrum_pass_count={search['spectrum_pass_count']}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
