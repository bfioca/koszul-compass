#!/usr/bin/env python3
"""Scout one move beyond selected radius-4 q=1 candidate records."""

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
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    apply_monoid_obstruction_override,
)
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


WINDOW_GLOBS = [
    "phenomenology_guided_q1_radius4_adjacency_scout_window*.json",
    "phenomenology_guided_q1_radius4_adjacency_scout_batch2_window*.json",
    "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window*.json",
    "phenomenology_guided_q1_radius4_adjacency_scout_batch4_window*.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_id(record: dict[str, Any], report: Path) -> str:
    return f"{report.name}:{record['label']}"


def source_priority(item: dict[str, Any]) -> tuple[Any, ...]:
    record = item["record"]
    prediction = record["spectrum_certificate"]["vectorlike_prediction"]
    classification = record["classification"]
    return (
        not record["spectrum_certificate"]["desired_q1_three_family_signature"],
        prediction.get("h2_wedge2_regular_multiplicity") is None,
        prediction.get("h2_wedge2_regular_multiplicity", 99),
        classification["status"] not in {
            "negative_control_doublet_triplet_obstruction",
            "dangerous_10_5bar_5bar_operator_allowed",
            "no_triplet_mass_in_certified_singlet_monoid",
            "no_certified_triplet_mass_operator_found",
        },
        max_abs_charge(record["matrix"]),
        item["id"],
    )


def load_radius4_sources() -> list[dict[str, Any]]:
    seen: set[tuple[tuple[int, ...], ...]] = set()
    sources = []
    for pattern in WINDOW_GLOBS:
        for path in sorted(REPORTS.glob(pattern)):
            report = load_json(path)
            if not report.get("all_gates_pass", False):
                continue
            for record in report.get("filtered_candidate_records", []):
                if not record["spectrum_certificate"]["desired_q1_three_family_signature"]:
                    continue
                key = matrix_key(record["matrix"])
                if key in seen:
                    continue
                seen.add(key)
                sources.append(
                    {
                        "id": source_id(record, path),
                        "report": str(path),
                        "record": record,
                    }
                )
    sources.sort(key=source_priority)
    return sources


def priority_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        max_abs_charge(item["matrix"]),
        item["source_status"] != "negative_control_doublet_triplet_obstruction",
        item["source_status"] != "dangerous_10_5bar_5bar_operator_allowed",
        item["source_id"],
        json.dumps(item["new_move"], sort_keys=True),
    )


def build_adjacency_frontier(
    *,
    source_records: list[dict[str, Any]],
    primitives: list[dict[str, Any]],
    max_abs_charge_bound: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    seen: set[tuple[tuple[int, ...], ...]] = set()
    frontier = []
    counters = {
        "source_radius4_records": len(source_records),
        "primitive_count": len(primitives),
        "raw_edges": 0,
        "unique_candidates": 0,
        "duplicate_up_to_summand_permutation": 0,
        "within_charge_bound": 0,
        "rejected_charge_bound": 0,
    }
    for source in source_records:
        source_record = source["record"]
        for primitive in primitives:
            counters["raw_edges"] += 1
            matrix = apply_moves(source_record["matrix"], [primitive])
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
                    "source_id": source["id"],
                    "source_report": source["report"],
                    "source_label": source_record["label"],
                    "source_status": source_record["classification"]["status"],
                    "source_prediction": source_record["spectrum_certificate"][
                        "vectorlike_prediction"
                    ],
                    "new_move": primitive,
                    "matrix": matrix,
                }
            )
    frontier.sort(key=priority_key)
    return frontier, counters


def build_report(
    *,
    max_abs_charge_bound: int,
    source_start: int,
    source_limit: int,
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
    no_go = load_json(REPORTS / "phenomenology_guided_q1_radius4_selected_branch_closed_no_go.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    primitives = [*row_transfer_primitives(), *rectangle_primitives()]

    all_sources = load_radius4_sources()
    source_records = all_sources[source_start:]
    if source_limit > 0:
        source_records = source_records[:source_limit]

    adjacency, adjacency_counters = build_adjacency_frontier(
        source_records=source_records,
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
    raw_q1_records = []
    cohomology_exception_samples = []

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
                        "source_id": item["source_id"],
                        "source_status": item["source_status"],
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
            label=f"radius5_adjacency_certified_{index}",
            matrix=raw["matrix"],
            move=[raw["new_move"]],
            slope_restarts=certification_restarts,
            slope_seed=seed + 900000 + index,
        )
        certified["radius5_source_id"] = raw["source_id"]
        certified["radius5_source_status"] = raw["source_status"]
        certified["radius5_new_move"] = raw["new_move"]
        if certified["character_certified"]:
            counters["character_certified_q1_survivors"] += 1
        certified_records.append(certified)
        filtered = candidate_certificate_from_5259_record(
            label=f"radius5_adjacency_filtered_{index}",
            record=certified,
            conf=conf,
        )
        apply_monoid_obstruction_override(filtered)
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
        filtered["radius5_source_id"] = raw["source_id"]
        filtered["radius5_source_status"] = raw["source_status"]
        filtered["radius5_new_move"] = raw["new_move"]
        filtered_records.append(filtered)

    categories: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for record in filtered_records:
        category = record["classification"]["category"]
        status = record["classification"]["status"]
        categories[category] = categories.get(category, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1

    viable = [
        record for record in filtered_records if record["classification"]["category"] == "viable"
    ]
    gates = {
        "imports_radius4_no_go": gate(
            no_go["all_gates_pass"]
            and no_go["summary"]["viable_count"] == 0
            and no_go["summary"]["raw_q1_spectrum_survivors"] == 200,
            str(REPORTS / "phenomenology_guided_q1_radius4_selected_branch_closed_no_go.json"),
            "radius5 scout starts only after the selected radius4 surface is closed",
        ),
        "source_records_loaded": gate(
            len(all_sources) >= len(source_records) > 0,
            "radius4 window filtered_candidate_records",
            "radius5 scout loads actual selected radius4 q=1 source matrices",
        ),
        "screening_window_nonempty": gate(
            len(screened) > 0,
            "radius5 adjacency frontier window",
            "the configured radius5 adjacency window is nonempty",
        ),
        "certification_budget_respected": gate(
            counters["raw_q1_certification_attempts"]
            == min(counters["raw_q1_spectrum_survivors"], max_raw_q1_to_certify),
            "radius5 raw q1 certification budget",
            "the certification pass attempted the configured number of raw q1 survivors",
        ),
    }
    return {
        "scope": "bounded radius5 adjacency scout from selected radius4 q=1 source records",
        "status": (
            "viable_candidate_found_in_radius5_adjacency_scout"
            if viable
            else "no_viable_candidate_found_in_radius5_adjacency_scout_window"
        ),
        "search_parameters": {
            "max_abs_charge_bound": max_abs_charge_bound,
            "source_start": source_start,
            "source_limit": source_limit,
            "frontier_start": frontier_start,
            "max_frontier_to_screen": max_frontier_to_screen,
            "max_raw_q1_to_certify": max_raw_q1_to_certify,
            "slope_restarts": slope_restarts,
            "slope_max_iterations": slope_max_iterations,
            "certification_restarts": certification_restarts,
            "seed": seed,
        },
        "source_summary": {
            "available_radius4_q1_sources": len(all_sources),
            "selected_source_records": len(source_records),
            "selected_source_ids": [item["id"] for item in source_records],
        },
        "adjacency_counters": adjacency_counters,
        "screening_counters": counters,
        "rejection_counters": dict(sorted(rejection_counters.items())),
        "summary": {
            "raw_q1_spectrum_survivors": counters["raw_q1_spectrum_survivors"],
            "certified_q1_records": len(filtered_records),
            "character_certified_q1_survivors": counters[
                "character_certified_q1_survivors"
            ],
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
            "viable_count": len(viable),
        },
        "raw_q1_records": raw_q1_records,
        "certified_records": certified_records,
        "filtered_candidate_records": filtered_records,
        "cohomology_exception_samples": cohomology_exception_samples,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-5 Adjacency Scout",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Sources", ""])
    for source in report["source_summary"]["selected_source_ids"]:
        lines.append(f"- `{source}`")
    lines.extend(["", "## Screening", ""])
    for key, value in report["screening_counters"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Classifications", ""])
    for record in report["filtered_candidate_records"]:
        lines.append(
            f"- `{record['label']}` from `{record['radius5_source_id']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; prediction "
            f"`{record['spectrum_certificate']['vectorlike_prediction']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-abs-charge-bound", type=int, default=4)
    parser.add_argument("--source-start", type=int, default=0)
    parser.add_argument("--source-limit", type=int, default=8)
    parser.add_argument("--frontier-start", type=int, default=0)
    parser.add_argument("--max-frontier-to-screen", type=int, default=1600)
    parser.add_argument("--max-raw-q1-to-certify", type=int, default=30)
    parser.add_argument("--slope-restarts", type=int, default=8)
    parser.add_argument("--slope-max-iterations", type=int, default=1500)
    parser.add_argument("--certification-restarts", type=int, default=32)
    parser.add_argument("--seed", type=int, default=525900)
    parser.add_argument("--progress-every", type=int, default=0)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout.md"),
    )
    args = parser.parse_args()
    report = build_report(
        max_abs_charge_bound=args.max_abs_charge_bound,
        source_start=args.source_start,
        source_limit=args.source_limit,
        frontier_start=args.frontier_start,
        max_frontier_to_screen=args.max_frontier_to_screen,
        max_raw_q1_to_certify=args.max_raw_q1_to_certify,
        slope_restarts=args.slope_restarts,
        slope_max_iterations=args.slope_max_iterations,
        certification_restarts=args.certification_restarts,
        seed=args.seed,
        progress_every=args.progress_every,
    )
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
