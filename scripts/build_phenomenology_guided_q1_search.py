#!/usr/bin/env python3
"""Search the q=1 5259/7914 neighborhood with the phenomenology filter."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_h2_frontier_search import (  # noqa: E402
    apply_moves,
    matrix_key,
    max_abs_charge,
    rectangle_primitives,
    row_transfer_primitives,
)
from build_phenomenology_filter_report import (  # noqa: E402
    candidate_certificate_from_5259_record,
)
from build_vectorlike_obstruction_report import certify_5259_matrix, gate  # noqa: E402
from string_theory.cicy import (  # noqa: E402
    bundle_c1,
    bundle_c2,
    bundle_index,
    triple_intersections,
    wedge2_index,
)
from string_theory.slope import find_slope_zero, intersection_tensor  # noqa: E402
from verify_family_candidate import cohomology_and_spectrum  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def move_family_summary(moves: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for move in moves:
        counts[move["family"]] += 1
    return dict(sorted(counts.items()))


def raw_q1_signature(cohomology: dict[str, Any]) -> bool:
    return (
        cohomology["V_cohomology"] == [0, 6, 0, 0]
        and cohomology["V_dual_cohomology"] == [0, 0, 6, 0]
        and cohomology["wedge2_V_cohomology"] == [0, 8, 2, 0]
        and cohomology["wedge2_V_dual_cohomology"] == [0, 2, 8, 0]
    )


def build_report(
    *,
    slope_restarts: int,
    slope_max_iterations: int,
    certification_restarts: int,
    seed: int,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    frontier = load_json(REPORTS / "cicy5259_h2_frontier_radius1_target.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    start = frontier["best_character_certified_record"]
    start_matrix = start["matrix"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    primitives = [*row_transfer_primitives(), *rectangle_primitives()]
    sequences: list[list[dict[str, Any]]] = [[]]
    sequences.extend([primitive] for primitive in primitives)

    counters = {
        "unique_candidates": 0,
        "within_charge_bound": 0,
        "c1_survivors": 0,
        "index_survivors": 0,
        "anomaly_survivors": 0,
        "slope_survivors": 0,
        "spectrum_survivors": 0,
        "raw_q1_spectrum_survivors": 0,
        "character_certified_q1_survivors": 0,
    }
    rejections: dict[str, int] = defaultdict(int)
    seen: set[tuple[tuple[int, ...], ...]] = set()
    raw_q1_records = []

    for index, moves in enumerate(sequences):
        matrix = apply_moves(start_matrix, moves)
        key = matrix_key(matrix)
        if key in seen:
            rejections["duplicate_up_to_summand_permutation"] += 1
            continue
        seen.add(key)
        counters["unique_candidates"] += 1
        if max_abs_charge(matrix) > 3:
            rejections["charge_bound"] += 1
            continue
        counters["within_charge_bound"] += 1
        try:
            if bundle_c1(matrix) != [0] * 7:
                rejections["c1"] += 1
                continue
            counters["c1_survivors"] += 1
            if bundle_index(matrix, intersections, c2_tx) != -6:
                rejections["index_v"] += 1
                continue
            if wedge2_index(matrix, intersections, c2_tx) != -6:
                rejections["index_wedge2_v"] += 1
                continue
            counters["index_survivors"] += 1
            c2_v = bundle_c2(matrix, intersections)
        except Exception:
            rejections["topology_exception"] += 1
            continue
        anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
        if not all(value >= 0 for value in anomaly):
            rejections["anomaly"] += 1
            continue
        counters["anomaly_survivors"] += 1
        slope = find_slope_zero(
            matrix,
            tensor,
            tolerance=1e-7,
            restarts=slope_restarts,
            max_iterations=slope_max_iterations,
            seed=seed + index,
        )
        if not slope.feasible:
            rejections["slope"] += 1
            continue
        counters["slope_survivors"] += 1
        cohomology = cohomology_and_spectrum(
            {"Num": 7914, "H11": 7, "Conf": conf, "C2": c2_tx},
            2,
            matrix,
        )
        spectrum = cohomology["su5_upstairs_spectrum"]
        quality = cohomology["line_bundle_sum_quality"]
        if (
            not all(spectrum["checks"].values())
            or spectrum["upstairs_anti_10"] != 0
            or not quality["regular_nontrivial_summand_scan_style"]
        ):
            rejections["spectrum_or_quality"] += 1
            continue
        counters["spectrum_survivors"] += 1
        if not raw_q1_signature(cohomology):
            rejections["not_raw_q1_signature"] += 1
            continue
        counters["raw_q1_spectrum_survivors"] += 1
        raw_q1_records.append(
            {
                "label": f"q1_neighborhood_raw_{len(raw_q1_records)}",
                "moves_from_q1_target": moves,
                "move_families": move_family_summary(moves),
                "matrix": matrix,
                "anomaly": anomaly,
                "slope_search": slope.as_dict(),
                "cohomology": {
                    "V": cohomology["V_cohomology"],
                    "V_dual": cohomology["V_dual_cohomology"],
                    "wedge2_V": cohomology["wedge2_V_cohomology"],
                    "wedge2_V_dual": cohomology["wedge2_V_dual_cohomology"],
                },
            }
        )

    certified_records = []
    filtered_records = []
    for index, raw in enumerate(raw_q1_records):
        certified = certify_5259_matrix(
            label=f"q1_neighborhood_certified_{index}",
            matrix=raw["matrix"],
            move=raw["moves_from_q1_target"],
            slope_restarts=certification_restarts,
            slope_seed=seed + 900000 + index,
        )
        certified["moves_from_q1_target"] = raw["moves_from_q1_target"]
        certified["move_families_from_q1_target"] = raw["move_families"]
        if certified["character_certified"]:
            counters["character_certified_q1_survivors"] += 1
        certified_records.append(certified)
        filtered = candidate_certificate_from_5259_record(
            label=f"q1_neighborhood_filtered_{index}",
            record=certified,
            conf=conf,
        )
        if not certified["character_certified"]:
            filtered["spectrum_certificate"][
                "desired_q1_three_family_signature"
            ] = True
            filtered["classification"] = {
                "category": "unresolved",
                "status": "missing_character_or_charge_level_data",
                "reason": (
                    "candidate has the raw q=1 cohomology signature but lacks a "
                    "complete character certificate for the phenomenology filter"
                ),
            }
        filtered_records.append(filtered)

    categories: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for record in filtered_records:
        category = record["classification"]["category"]
        status = record["classification"]["status"]
        categories[category] = categories.get(category, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1
    viable = [
        record
        for record in filtered_records
        if record["classification"]["category"] == "viable"
    ]
    unresolved = [
        record
        for record in filtered_records
        if record["classification"]["category"] == "unresolved"
    ]

    gates = {
        "search_started_from_certified_q1_target": gate(
            start["character_certified"]
            and start["vectorlike_pair_prediction"][
                "h2_wedge2_regular_multiplicity"
            ]
            == 1,
            str(REPORTS / "cicy5259_h2_frontier_radius1_target.json"),
            "local search starts from the certified q=1 5259/7914 target",
        ),
        "raw_q1_survivors_submitted_to_certification": gate(
            counters["raw_q1_spectrum_survivors"] == len(certified_records),
            "q=1 neighborhood certification queue",
            "every raw q=1 survivor in the bounded neighborhood was submitted to character certification",
        ),
        "phenomenology_filter_applied": gate(
            len(filtered_records) == len(certified_records)
            and all(
                record["mass_operator_table"] is not None
                and record["proton_decay_operator_table"] is not None
                for record in filtered_records
                if record["character_certificate"]["character_certified"]
            ),
            "phenomenology filter output",
            "every character-certified q=1 survivor received mass and proton-decay operator tables; uncertified raw q=1 survivors remain unresolved",
        ),
        "no_viable_candidate_in_this_neighborhood": gate(
            not viable,
            "q=1 neighborhood classifications",
            "no candidate in this bounded q=1 neighborhood passes the current charge-level filter",
        ),
    }

    return {
        "scope": "phenomenology-guided radius-1 search around the CICY 5259/7914 q=1 target",
        "search_parameters": {
            "start": "cicy5259_h2_frontier_radius1_target.best_character_certified_record",
            "move_radius": 1,
            "primitive_families": [
                "two_column_row_transfer",
                "paired_row_column_rectangle",
            ],
            "max_abs_charge": 3,
            "slope_restarts": slope_restarts,
            "slope_max_iterations": slope_max_iterations,
            "certification_restarts": certification_restarts,
            "seed": seed,
        },
        "counters": counters,
        "rejections": dict(sorted(rejections.items())),
        "raw_q1_records": raw_q1_records,
        "certified_records": certified_records,
        "filtered_candidate_records": filtered_records,
        "summary": {
            "raw_q1_count": len(raw_q1_records),
            "character_certified_q1_count": counters[
                "character_certified_q1_survivors"
            ],
            "viable_count": len(viable),
            "unresolved_count": len(unresolved),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
            "status": (
                "viable_candidate_found" if viable else "no_viable_candidate_found"
            ),
        },
        "gates": gates,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phenomenology-Guided Q1 Neighborhood Search",
        "",
        f"Status: `{report['summary']['status']}`",
        "",
        "## Search",
        "",
        f"- start: `{report['search_parameters']['start']}`",
        f"- move radius: `{report['search_parameters']['move_radius']}`",
        f"- primitive families: `{report['search_parameters']['primitive_families']}`",
        f"- counters: `{report['counters']}`",
        f"- rejections: `{report['rejections']}`",
        "",
        "## Summary",
        "",
        f"- raw q=1 count: `{report['summary']['raw_q1_count']}`",
        f"- character-certified q=1 count: `{report['summary']['character_certified_q1_count']}`",
        f"- viable count: `{report['summary']['viable_count']}`",
        f"- unresolved count: `{report['summary']['unresolved_count']}`",
        f"- categories: `{report['summary']['categories']}`",
        f"- statuses: `{report['summary']['statuses']}`",
        "",
        "## Candidate Classifications",
        "",
    ]
    for record in report["filtered_candidate_records"]:
        lines.append(
            f"- `{record['label']}`: `{record['classification']['category']}` / "
            f"`{record['classification']['status']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slope-restarts", type=int, default=4)
    parser.add_argument("--slope-max-iterations", type=int, default=900)
    parser.add_argument("--certification-restarts", type=int, default=20)
    parser.add_argument("--seed", type=int, default=991000)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_search.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_search.md"),
    )
    args = parser.parse_args()
    report = build_report(
        slope_restarts=args.slope_restarts,
        slope_max_iterations=args.slope_max_iterations,
        certification_restarts=args.certification_restarts,
        seed=args.seed,
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['summary']['status']}")
    print(f"raw_q1_count={report['summary']['raw_q1_count']}")
    print(
        "character_certified_q1_count="
        f"{report['summary']['character_certified_q1_count']}"
    )
    print(f"viable_count={report['summary']['viable_count']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
