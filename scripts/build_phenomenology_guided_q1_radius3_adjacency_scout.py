#!/usr/bin/env python3
"""Scout one move beyond the closed radius-2 q=1 obstruction frontier.

The full radius-3 move graph is large.  This bounded scout expands the 29
radius-2 q=1 attempts by one primitive move, deduplicates by summand
permutation, and applies the same charge-level obstruction filter to raw q=1
survivors that can be character-certified.
"""

from __future__ import annotations

import argparse
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
    counts: dict[str, int] = {}
    for move in moves:
        counts[move["family"]] = counts.get(move["family"], 0) + 1
    return dict(sorted(counts.items()))


def priority_key(item: dict[str, Any]) -> tuple[Any, ...]:
    matrix = item["matrix"]
    return (
        max_abs_charge(matrix),
        item["source_obstruction_status"] != "negative_control_doublet_triplet_obstruction",
        item["source_raw_candidate_key"],
        json.dumps(item["new_move"], sort_keys=True),
    )


def build_adjacency_frontier(
    *,
    radius2_records: list[dict[str, Any]],
    primitives: list[dict[str, Any]],
    max_abs_charge_bound: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    seen: set[tuple[tuple[int, ...], ...]] = set()
    frontier: list[dict[str, Any]] = []
    counters = {
        "source_radius2_records": len(radius2_records),
        "primitive_count": len(primitives),
        "raw_edges": 0,
        "unique_candidates": 0,
        "duplicate_up_to_summand_permutation": 0,
        "within_charge_bound": 0,
        "rejected_charge_bound": 0,
    }
    for source in radius2_records:
        source_matrix = source["matrix"]
        for primitive in primitives:
            counters["raw_edges"] += 1
            matrix = apply_moves(source_matrix, [primitive])
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
            frontier.append(
                {
                    "source_raw_candidate_key": source["raw_candidate_key"],
                    "source_final_resolution_label": source["final_resolution_label"],
                    "source_obstruction_status": source["classification"]["status"],
                    "new_move": primitive,
                    "matrix": matrix,
                }
            )
    frontier.sort(key=priority_key)
    return frontier, counters


def build_report(
    *,
    max_abs_charge_bound: int,
    frontier_start: int,
    max_frontier_to_screen: int,
    max_raw_q1_to_certify: int,
    slope_restarts: int,
    slope_max_iterations: int,
    certification_restarts: int,
    seed: int,
    progress_every: int,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    radius2 = load_json(REPORTS / "phenomenology_guided_q1_radius2_obstruction_filter_certificate.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    primitives = [*row_transfer_primitives(), *rectangle_primitives()]

    adjacency, adjacency_counters = build_adjacency_frontier(
        radius2_records=radius2["candidate_records"],
        primitives=primitives,
        max_abs_charge_bound=max_abs_charge_bound,
    )
    screened = adjacency[frontier_start : frontier_start + max_frontier_to_screen]
    counters = {
        "frontier_start": frontier_start,
        "frontier_records_screened": len(screened),
        "frontier_records_before_window": min(frontier_start, len(adjacency)),
        "frontier_records_after_window": max(
            0, len(adjacency) - frontier_start - len(screened)
        ),
        "frontier_records_unscreened": max(0, len(adjacency) - len(screened)),
        "c1_survivors": 0,
        "index_survivors": 0,
        "anomaly_survivors": 0,
        "slope_survivors": 0,
        "spectrum_survivors": 0,
        "raw_q1_spectrum_survivors": 0,
        "raw_q1_certification_attempts": 0,
        "character_certified_q1_survivors": 0,
        "cohomology_exceptions": 0,
        "topology_exceptions": 0,
    }
    rejection_counters: dict[str, int] = {}
    raw_q1_records: list[dict[str, Any]] = []
    cohomology_exception_samples: list[dict[str, Any]] = []

    for index, item in enumerate(screened):
        try:
            if bundle_c1(item["matrix"]) != [0] * 7:
                rejection_counters["c1"] = rejection_counters.get("c1", 0) + 1
                continue
            counters["c1_survivors"] += 1
            index_v = bundle_index(item["matrix"], intersections, c2_tx)
            index_wedge = wedge2_index(item["matrix"], intersections, c2_tx)
            if index_v != -6 or index_wedge != -6:
                rejection_counters["index"] = rejection_counters.get("index", 0) + 1
                continue
            counters["index_survivors"] += 1
            c2_v = bundle_c2(item["matrix"], intersections)
        except Exception:
            counters["topology_exceptions"] += 1
            continue
        anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
        if not all(value >= 0 for value in anomaly):
            rejection_counters["anomaly"] = rejection_counters.get("anomaly", 0) + 1
            continue
        counters["anomaly_survivors"] += 1
        slope = find_slope_zero(
            item["matrix"],
            tensor,
            tolerance=1e-7,
            restarts=slope_restarts,
            max_iterations=slope_max_iterations,
            seed=seed + index,
        )
        if not slope.feasible:
            rejection_counters["slope"] = rejection_counters.get("slope", 0) + 1
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
            if len(cohomology_exception_samples) < 12:
                cohomology_exception_samples.append(
                    {
                        "source_raw_candidate_key": item["source_raw_candidate_key"],
                        "source_obstruction_status": item[
                            "source_obstruction_status"
                        ],
                        "new_move": item["new_move"],
                        "matrix": item["matrix"],
                        "exception": {
                            "type": type(error).__name__,
                            "message": str(error),
                        },
                    }
                )
            continue
        spectrum = cohomology["su5_upstairs_spectrum"]
        quality = cohomology["line_bundle_sum_quality"]
        if (
            not all(spectrum["checks"].values())
            or spectrum["upstairs_anti_10"] != 0
            or not quality["regular_nontrivial_summand_scan_style"]
        ):
            rejection_counters["spectrum_or_quality"] = (
                rejection_counters.get("spectrum_or_quality", 0) + 1
            )
            continue
        counters["spectrum_survivors"] += 1
        if not raw_q1_signature(cohomology):
            rejection_counters["not_raw_q1"] = rejection_counters.get("not_raw_q1", 0) + 1
            continue
        counters["raw_q1_spectrum_survivors"] += 1
        raw_q1_records.append(
            {
                **item,
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
        if progress_every and (index + 1) % progress_every == 0:
            print(
                "progress "
                f"screened={index + 1} "
                f"slope_survivors={counters['slope_survivors']} "
                f"raw_q1={len(raw_q1_records)}",
                flush=True,
            )

    certified_records = []
    filtered_records = []
    for index, raw in enumerate(raw_q1_records[:max_raw_q1_to_certify]):
        counters["raw_q1_certification_attempts"] += 1
        certified = certify_5259_matrix(
            label=f"radius3_adjacency_certified_{index}",
            matrix=raw["matrix"],
            move=[raw["new_move"]],
            slope_restarts=certification_restarts,
            slope_seed=seed + 900000 + index,
        )
        certified["radius3_source_raw_candidate_key"] = raw["source_raw_candidate_key"]
        certified["radius3_source_obstruction_status"] = raw["source_obstruction_status"]
        certified["radius3_new_move"] = raw["new_move"]
        if certified["character_certified"]:
            counters["character_certified_q1_survivors"] += 1
        certified_records.append(certified)
        filtered = candidate_certificate_from_5259_record(
            label=f"radius3_adjacency_filtered_{index}",
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
        filtered["radius3_source_raw_candidate_key"] = raw["source_raw_candidate_key"]
        filtered["radius3_source_obstruction_status"] = raw["source_obstruction_status"]
        filtered["radius3_new_move"] = raw["new_move"]
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
        "radius2_certificate_imported": gate(
            radius2["summary"]["raw_q1_attempts"] == 29
            and radius2["summary"]["viable"] == 0
            and radius2["summary"]["unresolved"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius2_obstruction_filter_certificate.json"),
            "scout expands the closed radius-2 q=1 obstruction ledger",
        ),
        "adjacency_frontier_generated": gate(
            adjacency_counters["raw_edges"] == 29 * len(primitives)
            and adjacency_counters["unique_candidates"] > 0
            and len(screened) > 0,
            "radius-3 adjacency frontier",
            "one additional primitive move was generated from every closed radius-2 q=1 record",
        ),
        "filter_tables_emitted_for_certified_records": gate(
            all(
                record["mass_operator_table"] is not None
                and record["proton_decay_operator_table"] is not None
                for record in filtered_records
                if record["character_certificate"]["character_certified"]
            ),
            "radius-3 filtered records",
            "every character-certified raw q=1 adjacency survivor has mass/proton tables",
        ),
        "viable_status_consistent": gate(
            (len(viable) > 0)
            == (any(record["classification"]["category"] == "viable" for record in filtered_records)),
            "radius-3 filtered records",
            "summary agrees with per-record viable classifications",
        ),
    }

    return {
        "scope": "bounded radius-3 adjacency scout from the closed radius-2 q=1 obstruction frontier",
        "status": "viable_candidate_found" if viable else "no_viable_candidate_found_in_bounded_radius3_adjacency_scout",
        "search_parameters": {
            "source": "phenomenology_guided_q1_radius2_obstruction_filter_certificate.json",
            "move_radius_interpretation": "one primitive move beyond each closed radius-2 q=1 attempt",
            "primitive_families": [
                "two_column_row_transfer",
                "paired_row_column_rectangle",
            ],
            "max_abs_charge_bound": max_abs_charge_bound,
            "frontier_start": frontier_start,
            "max_frontier_to_screen": max_frontier_to_screen,
            "max_raw_q1_to_certify": max_raw_q1_to_certify,
            "slope_restarts": slope_restarts,
            "slope_max_iterations": slope_max_iterations,
            "certification_restarts": certification_restarts,
            "seed": seed,
        },
        "adjacency_counters": adjacency_counters,
        "screening_counters": counters,
        "rejection_counters": dict(sorted(rejection_counters.items())),
        "raw_q1_records": raw_q1_records,
        "cohomology_exception_samples": cohomology_exception_samples,
        "certified_records": certified_records,
        "filtered_candidate_records": filtered_records,
        "summary": {
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Adjacency Q1 Scout",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Scope",
        "",
        "This is a bounded one-move expansion window from the closed radius-2 q=1 obstruction ledger, not a full radius-3 no-go.",
        "",
        "## Counts",
        "",
        f"- adjacency counters: `{report['adjacency_counters']}`",
        f"- screening counters: `{report['screening_counters']}`",
        f"- rejection counters: `{report['rejection_counters']}`",
        f"- categories: `{report['summary']['categories']}`",
        f"- statuses: `{report['summary']['statuses']}`",
        f"- viable count: `{report['summary']['viable_count']}`",
        "",
        "## Candidate Classifications",
        "",
    ]
    for record in report["filtered_candidate_records"]:
        lines.append(
            "- "
            f"`{record['label']}` from `{record['radius3_source_raw_candidate_key']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-abs-charge", type=int, default=4)
    parser.add_argument("--frontier-start", type=int, default=0)
    parser.add_argument("--max-frontier-to-screen", type=int, default=4000)
    parser.add_argument("--max-raw-q1-to-certify", type=int, default=40)
    parser.add_argument("--slope-restarts", type=int, default=6)
    parser.add_argument("--slope-max-iterations", type=int, default=1200)
    parser.add_argument("--certification-restarts", type=int, default=20)
    parser.add_argument("--seed", type=int, default=525979143)
    parser.add_argument("--progress-every", type=int, default=0)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout.md"),
    )
    args = parser.parse_args()
    report = build_report(
        max_abs_charge_bound=args.max_abs_charge,
        frontier_start=args.frontier_start,
        max_frontier_to_screen=args.max_frontier_to_screen,
        max_raw_q1_to_certify=args.max_raw_q1_to_certify,
        slope_restarts=args.slope_restarts,
        slope_max_iterations=args.slope_max_iterations,
        certification_restarts=args.certification_restarts,
        seed=args.seed,
        progress_every=args.progress_every,
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(f"adjacency_counters={report['adjacency_counters']}")
    print(f"screening_counters={report['screening_counters']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
