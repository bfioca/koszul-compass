#!/usr/bin/env python3
"""Bounded radius-2 pilot search for phenomenologically viable q=1 candidates."""

from __future__ import annotations

import argparse
from itertools import combinations
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
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_search import raw_q1_signature  # noqa: E402
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
    out: dict[str, int] = {}
    for move in moves:
        out[move["family"]] = out.get(move["family"], 0) + 1
    return dict(sorted(out.items()))


def move_priority(moves: list[dict[str, Any]], matrix: list[list[int]]) -> tuple[Any, ...]:
    families = move_family_summary(moves)
    rectangle_count = families.get("paired_row_column_rectangle", 0)
    row_transfer_count = families.get("two_column_row_transfer", 0)
    touched_rows = set()
    touched_cols = set()
    for move in moves:
        if move["family"] == "two_column_row_transfer":
            touched_rows.add(move["row"])
            touched_cols.update(move["columns"])
        else:
            touched_rows.update(move["rows"])
            touched_cols.update(move["columns"])
    return (
        max_abs_charge(matrix),
        rectangle_count,
        row_transfer_count,
        len(touched_rows),
        len(touched_cols),
        json.dumps(moves, sort_keys=True),
    )


def build_anomaly_frontier(
    *,
    base: list[list[int]],
    primitives: list[dict[str, Any]],
    intersections: dict[tuple[int, int, int], int],
    c2_tx: list[int],
    max_abs_charge_bound: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    seen: set[tuple[tuple[int, ...], ...]] = set()
    counters = {
        "unique_candidates": 0,
        "within_charge_bound": 0,
        "c1_survivors": 0,
        "index_survivors": 0,
        "anomaly_survivors": 0,
        "duplicate_up_to_summand_permutation": 0,
        "rejected_charge_bound": 0,
        "rejected_c1": 0,
        "rejected_index": 0,
        "rejected_anomaly": 0,
        "topology_exception": 0,
    }
    frontier = []
    sequences = [()]
    sequences.extend((index,) for index in range(len(primitives)))
    sequences.extend(combinations(range(len(primitives)), 2))
    for indices in sequences:
        moves = [primitives[index] for index in indices]
        matrix = apply_moves(base, moves)
        key = matrix_key(matrix)
        if key in seen:
            counters["duplicate_up_to_summand_permutation"] += 1
            continue
        seen.add(key)
        counters["unique_candidates"] += 1
        if max_abs_charge(matrix) > max_abs_charge_bound:
            counters["rejected_charge_bound"] += 1
            continue
        counters["within_charge_bound"] += 1
        try:
            if bundle_c1(matrix) != [0] * 7:
                counters["rejected_c1"] += 1
                continue
            counters["c1_survivors"] += 1
            if (
                bundle_index(matrix, intersections, c2_tx) != -6
                or wedge2_index(matrix, intersections, c2_tx) != -6
            ):
                counters["rejected_index"] += 1
                continue
            counters["index_survivors"] += 1
            c2_v = bundle_c2(matrix, intersections)
        except Exception:
            counters["topology_exception"] += 1
            continue
        anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
        if not all(value >= 0 for value in anomaly):
            counters["rejected_anomaly"] += 1
            continue
        counters["anomaly_survivors"] += 1
        frontier.append(
            {
                "moves": moves,
                "move_families": move_family_summary(moves),
                "matrix": matrix,
                "anomaly": anomaly,
                "priority": move_priority(moves, matrix),
            }
        )
    frontier.sort(key=lambda item: item["priority"])
    return frontier, counters


def build_report(
    *,
    max_abs_charge: int,
    anomaly_start: int,
    max_anomaly_to_screen: int,
    max_raw_q1_to_certify: int,
    slope_restarts: int,
    slope_max_iterations: int,
    certification_restarts: int,
    seed: int,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    start_report = load_json(REPORTS / "cicy5259_h2_frontier_radius1_target.json")
    start = start_report["best_character_certified_record"]
    base = start["matrix"]
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    primitives = [*row_transfer_primitives(), *rectangle_primitives()]
    anomaly_frontier, topology_counters = build_anomaly_frontier(
        base=base,
        primitives=primitives,
        intersections=intersections,
        c2_tx=c2_tx,
        max_abs_charge_bound=max_abs_charge,
    )
    screened = anomaly_frontier[anomaly_start : anomaly_start + max_anomaly_to_screen]
    counters = {
        "anomaly_frontier_size": len(anomaly_frontier),
        "anomaly_start": anomaly_start,
        "anomaly_records_screened": len(screened),
        "anomaly_records_before_window": min(anomaly_start, len(anomaly_frontier)),
        "anomaly_records_after_window": max(
            0, len(anomaly_frontier) - anomaly_start - len(screened)
        ),
        "anomaly_records_unscreened": max(0, len(anomaly_frontier) - len(screened)),
        "slope_survivors": 0,
        "spectrum_survivors": 0,
        "raw_q1_spectrum_survivors": 0,
        "raw_q1_certification_attempts": 0,
        "character_certified_q1_survivors": 0,
        "cohomology_exceptions": 0,
    }
    raw_q1_records = []
    for index, item in enumerate(screened):
        slope = find_slope_zero(
            item["matrix"],
            tensor,
            tolerance=1e-7,
            restarts=slope_restarts,
            max_iterations=slope_max_iterations,
            seed=seed + index,
        )
        if not slope.feasible:
            continue
        counters["slope_survivors"] += 1
        try:
            cohomology = cohomology_and_spectrum(
                {"Num": 7914, "H11": 7, "Conf": conf, "C2": c2_tx},
                2,
                item["matrix"],
            )
        except Exception as error:
            counters["cohomology_exceptions"] += 1
            item["cohomology_exception"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
            continue
        spectrum = cohomology["su5_upstairs_spectrum"]
        quality = cohomology["line_bundle_sum_quality"]
        if (
            not all(spectrum["checks"].values())
            or spectrum["upstairs_anti_10"] != 0
            or not quality["regular_nontrivial_summand_scan_style"]
        ):
            continue
        counters["spectrum_survivors"] += 1
        if not raw_q1_signature(cohomology):
            continue
        counters["raw_q1_spectrum_survivors"] += 1
        raw_q1_records.append(
            {
                **item,
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
    for index, raw in enumerate(raw_q1_records[:max_raw_q1_to_certify]):
        counters["raw_q1_certification_attempts"] += 1
        certified = certify_5259_matrix(
            label=f"radius2_pilot_q1_certified_{index}",
            matrix=raw["matrix"],
            move=raw["moves"],
            slope_restarts=certification_restarts,
            slope_seed=seed + 900000 + index,
        )
        certified["moves_from_q1_target"] = raw["moves"]
        certified["move_families_from_q1_target"] = raw["move_families"]
        if certified["character_certified"]:
            counters["character_certified_q1_survivors"] += 1
        certified_records.append(certified)
        filtered = candidate_certificate_from_5259_record(
            label=f"radius2_pilot_filtered_{index}",
            record=certified,
            conf=conf,
        )
        if not certified["character_certified"]:
            filtered["spectrum_certificate"]["desired_q1_three_family_signature"] = True
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
    gates = {
        "pilot_has_explicit_frontier_denominator": gate(
            topology_counters["anomaly_survivors"] == len(anomaly_frontier)
            and len(anomaly_frontier) >= len(screened),
            "radius-2 topology/anomaly frontier",
            "pilot records total anomaly frontier and screened subset",
        ),
        "pilot_screened_nonzero_subset": gate(
            len(screened) > 0
            and counters["anomaly_records_screened"] <= max_anomaly_to_screen
            and anomaly_start < len(anomaly_frontier),
            "pilot parameters",
            "a bounded nonzero anomaly-frontier subset was screened",
        ),
        "phenomenology_filter_applied_to_certified_records": gate(
            len(filtered_records) == len(certified_records)
            and all(
                record["mass_operator_table"] is not None
                and record["proton_decay_operator_table"] is not None
                for record in filtered_records
                if record["character_certificate"]["character_certified"]
            ),
            "pilot q=1 certified records",
            "every character-certified raw q=1 pilot survivor has mass and proton tables",
        ),
    }
    return {
        "scope": "bounded radius-2 phenomenology-guided q=1 pilot around CICY 5259/7914 target",
        "search_parameters": {
            "move_radius": 2,
            "primitive_families": [
                "two_column_row_transfer",
                "paired_row_column_rectangle",
            ],
            "max_abs_charge": max_abs_charge,
            "anomaly_start": anomaly_start,
            "max_anomaly_to_screen": max_anomaly_to_screen,
            "max_raw_q1_to_certify": max_raw_q1_to_certify,
            "slope_restarts": slope_restarts,
            "slope_max_iterations": slope_max_iterations,
            "certification_restarts": certification_restarts,
            "seed": seed,
        },
        "topology_counters": topology_counters,
        "pilot_counters": counters,
        "raw_q1_records": raw_q1_records,
        "certified_records": certified_records,
        "filtered_candidate_records": filtered_records,
        "summary": {
            "status": "viable_candidate_found" if viable else "no_viable_candidate_found_in_pilot",
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
            "pilot_scope_note": (
                "This is a bounded pilot over the prioritized radius-2 anomaly frontier, "
                "not an exhaustive radius-2 no-go."
            ),
        },
        "gates": gates,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Phenomenology-Guided Q1 Pilot",
        "",
        f"Status: `{report['summary']['status']}`",
        "",
        "## Scope",
        "",
        report["summary"]["pilot_scope_note"],
        "",
        "## Counts",
        "",
        f"- topology counters: `{report['topology_counters']}`",
        f"- pilot counters: `{report['pilot_counters']}`",
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
    parser.add_argument("--max-abs-charge", type=int, default=3)
    parser.add_argument("--anomaly-start", type=int, default=0)
    parser.add_argument("--max-anomaly-to-screen", type=int, default=1200)
    parser.add_argument("--max-raw-q1-to-certify", type=int, default=40)
    parser.add_argument("--slope-restarts", type=int, default=3)
    parser.add_argument("--slope-max-iterations", type=int, default=700)
    parser.add_argument("--certification-restarts", type=int, default=18)
    parser.add_argument("--seed", type=int, default=992000)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_pilot.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_pilot.md"),
    )
    args = parser.parse_args()
    report = build_report(
        max_abs_charge=args.max_abs_charge,
        anomaly_start=args.anomaly_start,
        max_anomaly_to_screen=args.max_anomaly_to_screen,
        max_raw_q1_to_certify=args.max_raw_q1_to_certify,
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
    print(f"anomaly_frontier_size={report['pilot_counters']['anomaly_frontier_size']}")
    print(f"anomaly_start={report['pilot_counters']['anomaly_start']}")
    print(f"anomaly_records_screened={report['pilot_counters']['anomaly_records_screened']}")
    print(f"raw_q1_spectrum_survivors={report['pilot_counters']['raw_q1_spectrum_survivors']}")
    print(f"viable_count={report['summary']['viable_count']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
