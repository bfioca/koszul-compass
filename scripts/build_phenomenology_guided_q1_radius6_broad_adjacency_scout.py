#!/usr/bin/env python3
"""Scout one move beyond the verified broad radius-5 q=1 frontier."""

from __future__ import annotations

import argparse
from collections import Counter
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
    single_column_dipole_primitives,
)
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    apply_monoid_obstruction_override,
)
from phenomenology_guided_q1_representative_grammar_gate import (  # noqa: E402
    RepresentativeGrammarGate,
    apply_representative_grammar_boundary,
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


SCOUT_REPORTS = [
    REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout.json",
    REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout_window2.json",
    REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout_window3.json",
]
SCOUT_VERIFICATIONS = [
    REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout_verification.json",
    REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout_window2_verification.json",
    REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout_window3_verification.json",
]
BRANCH_REPORTS = [
    REPORTS / "phenomenology_guided_q1_radius5_branch_analysis.json",
    REPORTS / "phenomenology_guided_q1_radius5_branch_analysis_window2.json",
    REPORTS / "phenomenology_guided_q1_radius5_branch_analysis_window3.json",
    REPORTS / "phenomenology_guided_q1_radius5_window3_large_branch_closure.json",
]
BRANCH_VERIFICATIONS = [
    REPORTS / "phenomenology_guided_q1_radius5_branch_analysis_verification.json",
    REPORTS / "phenomenology_guided_q1_radius5_branch_analysis_window2_verification.json",
    REPORTS / "phenomenology_guided_q1_radius5_branch_analysis_window3_verification.json",
    REPORTS / "phenomenology_guided_q1_radius5_window3_large_branch_closure_verification.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sorted_window_paths(pattern: str) -> list[Path]:
    return sorted(
        (
            path
            for path in REPORTS.glob(pattern)
            if "verification" not in path.name and "partial_aggregate" not in path.name
        ),
        key=lambda path: path.name,
    )


def source_priority(source: dict[str, Any]) -> tuple[Any, ...]:
    return (
        max_abs_charge(source["matrix"]),
        source["source_status"] != "negative_control_doublet_triplet_obstruction",
        source["source_status"] != "dangerous_10_5bar_5bar_operator_allowed",
        source["source_id"],
    )


def add_source_record(
    *,
    record: dict[str, Any],
    source_id: str,
    source_file: Path,
    seen: set[tuple[tuple[int, ...], ...]],
    sources: list[dict[str, Any]],
) -> None:
    if not record["spectrum_certificate"]["desired_q1_three_family_signature"]:
        return
    key = matrix_key(record["matrix"])
    if key in seen:
        return
    seen.add(key)
    sources.append(
        {
            "source_id": source_id,
            "source_file": str(source_file),
            "source_status": record["classification"]["status"],
            "source_category": record["classification"]["category"],
            "matrix": record["matrix"],
        }
    )


def load_radius5_sources() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    verification_paths = [*SCOUT_VERIFICATIONS, *BRANCH_VERIFICATIONS]
    verifications = [load_json(path) for path in verification_paths]
    seen: set[tuple[tuple[int, ...], ...]] = set()
    sources = []

    for path in SCOUT_REPORTS:
        report = load_json(path)
        for record in report.get("filtered_candidate_records", []):
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
    for path in BRANCH_REPORTS:
        report = load_json(path)
        for record in report.get("desired_q1_branch_candidate_records", []):
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
        if "q1_representative_candidate" in report:
            record = report["q1_representative_candidate"]
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )

    sources.sort(key=source_priority)
    metadata = {
        "verification_paths": [str(path) for path in verification_paths],
        "verifications_pass": all(item["all_gates_pass"] for item in verifications),
        "source_count": len(sources),
    }
    return sources, metadata


def load_radius6_sources() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    verification_paths = [
        REPORTS / "phenomenology_guided_q1_radius6_broad_aggregate_verification.json"
    ]
    verifications = [load_json(path) for path in verification_paths]
    scout_paths = [
        REPORTS / "phenomenology_guided_q1_radius6_broad_adjacency_scout.json",
        *sorted_window_paths(
            "phenomenology_guided_q1_radius6_broad_adjacency_scout_window*.json"
        ),
    ]
    branch_paths = sorted_window_paths(
        "phenomenology_guided_q1_radius6_broad_branch_analysis_window*.json"
    )
    large_paths = sorted_window_paths(
        "phenomenology_guided_q1_radius6_broad_window*_large_branch_closure_*.json"
    )
    seen: set[tuple[tuple[int, ...], ...]] = set()
    sources = []
    for path in scout_paths:
        report = load_json(path)
        for record in report.get("filtered_candidate_records", []):
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
    for path in [*branch_paths, *large_paths]:
        report = load_json(path)
        for record in report.get("desired_q1_branch_candidate_records", []):
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
        if "q1_representative_candidate" in report:
            record = report["q1_representative_candidate"]
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
    sources.sort(key=source_priority)
    metadata = {
        "verification_paths": [str(path) for path in verification_paths],
        "verifications_pass": all(item["all_gates_pass"] for item in verifications),
        "source_count": len(sources),
        "source_reports_loaded": len(scout_paths) + len(branch_paths) + len(large_paths),
    }
    return sources, metadata


def load_radius7_sources() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    verification_paths = [
        REPORTS / "phenomenology_guided_q1_radius7_broad_frontier_rollup.json"
    ]
    verifications = [load_json(path) for path in verification_paths]
    scout_paths = sorted_window_paths(
        "phenomenology_guided_q1_radius7_broad_adjacency_scout_window*.json"
    )
    branch_paths = sorted_window_paths(
        "phenomenology_guided_q1_radius7_broad_branch_analysis_window*.json"
    )
    large_paths = sorted_window_paths(
        "phenomenology_guided_q1_radius7_broad_window*_large_branch_closure_*.json"
    )
    seen: set[tuple[tuple[int, ...], ...]] = set()
    sources = []
    for path in scout_paths:
        report = load_json(path)
        for record in report.get("filtered_candidate_records", []):
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
    for path in [*branch_paths, *large_paths]:
        report = load_json(path)
        for record in report.get("desired_q1_branch_candidate_records", []):
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
        if "q1_representative_candidate" in report:
            record = report["q1_representative_candidate"]
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
    sources.sort(key=source_priority)
    metadata = {
        "verification_paths": [str(path) for path in verification_paths],
        "verifications_pass": all(item["all_gates_pass"] for item in verifications),
        "source_count": len(sources),
        "source_reports_loaded": len(scout_paths) + len(branch_paths) + len(large_paths),
    }
    return sources, metadata


def load_radius8_sources() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    verification_paths = [
        REPORTS / "phenomenology_guided_q1_radius8_broad_windows1_50_rollup.json"
    ]
    verifications = [load_json(path) for path in verification_paths]
    scout_paths = sorted_window_paths(
        "phenomenology_guided_q1_radius8_broad_adjacency_scout_window*.json"
    )
    branch_paths = sorted_window_paths(
        "phenomenology_guided_q1_radius8_broad_branch_analysis_window*.json"
    )
    large_paths = [
        *sorted_window_paths(
            "phenomenology_guided_q1_radius8_broad_window*_large_branch_closure_*.json"
        ),
        *sorted_window_paths(
            "phenomenology_guided_q1_radius8_broad_large_branch_closure_window*_filtered_*.json"
        ),
    ]
    seen: set[tuple[tuple[int, ...], ...]] = set()
    sources = []
    for path in scout_paths:
        report = load_json(path)
        for record in report.get("filtered_candidate_records", []):
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
    for path in [*branch_paths, *large_paths]:
        report = load_json(path)
        for record in report.get("desired_q1_branch_candidate_records", []):
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
        if "q1_representative_candidate" in report:
            record = report["q1_representative_candidate"]
            add_source_record(
                record=record,
                source_id=f"{path.name}:{record['label']}",
                source_file=path,
                seen=seen,
                sources=sources,
            )
    sources.sort(key=source_priority)
    metadata = {
        "verification_paths": [str(path) for path in verification_paths],
        "verifications_pass": all(item["all_gates_pass"] for item in verifications),
        "source_count": len(sources),
        "source_reports_loaded": len(scout_paths) + len(branch_paths) + len(large_paths),
    }
    return sources, metadata


def load_sources(source_radius: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if source_radius == 5:
        sources, metadata = load_radius5_sources()
    elif source_radius == 6:
        sources, metadata = load_radius6_sources()
    elif source_radius == 7:
        sources, metadata = load_radius7_sources()
    elif source_radius == 8:
        sources, metadata = load_radius8_sources()
    else:
        raise ValueError(f"unsupported source radius {source_radius}")
    metadata = {**metadata, "source_radius": source_radius}
    return sources, metadata


def priority_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        max_abs_charge(item["matrix"]),
        item["source_status"] != "negative_control_doublet_triplet_obstruction",
        item["source_status"] != "dangerous_10_5bar_5bar_operator_allowed",
        item["source_id"],
        item["move"]["family"],
        json.dumps(item["move"], sort_keys=True),
    )


def build_frontier(
    sources: list[dict[str, Any]],
    primitives: list[dict[str, Any]],
    *,
    max_abs_charge_bound: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    counters = {
        "radius5_source_matrices": len(sources),
        "source_matrices": len(sources),
        "primitive_count": len(primitives),
        "raw_edges": 0,
        "unique_candidates": 0,
        "duplicate_up_to_summand_permutation": 0,
        "within_charge_bound": 0,
        "rejected_charge_bound": 0,
    }
    seen: set[tuple[tuple[int, ...], ...]] = set()
    frontier = []
    for source in sources:
        for primitive in primitives:
            counters["raw_edges"] += 1
            matrix = apply_moves(source["matrix"], [primitive])
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
                    "source_id": source["source_id"],
                    "source_file": source["source_file"],
                    "source_status": source["source_status"],
                    "source_category": source["source_category"],
                    "move": primitive,
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
    source_radius: int,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    sources, source_metadata = load_sources(source_radius)
    primitives = [
        *single_column_dipole_primitives(),
        *row_transfer_primitives(),
        *rectangle_primitives(),
    ]
    frontier, frontier_counters = build_frontier(
        sources, primitives, max_abs_charge_bound=max_abs_charge_bound
    )
    screened = frontier[frontier_start : frontier_start + max_frontier_to_screen]
    counters = {
        "frontier_start": frontier_start,
        "frontier_records_screened": len(screened),
        "frontier_records_after_window": max(
            0, len(frontier) - frontier_start - len(screened)
        ),
        "c1_survivors": 0,
        "index_survivors": 0,
        "anomaly_survivors": 0,
        "slope_survivors": 0,
        "spectrum_survivors": 0,
        "raw_q1_spectrum_survivors": 0,
        "raw_q1_certification_attempts": 0,
        "character_certified_q1_survivors": 0,
        "topology_exceptions": 0,
        "cohomology_exceptions": 0,
    }
    rejections: Counter[str] = Counter()
    raw_q1_records = []
    exception_samples = []
    for index, item in enumerate(screened):
        try:
            if bundle_c1(item["matrix"]) != [0] * 7:
                rejections["c1"] += 1
                continue
            counters["c1_survivors"] += 1
            if (
                bundle_index(item["matrix"], intersections, c2_tx) != -6
                or wedge2_index(item["matrix"], intersections, c2_tx) != -6
            ):
                rejections["index"] += 1
                continue
            counters["index_survivors"] += 1
            c2_v = bundle_c2(item["matrix"], intersections)
        except Exception as error:
            counters["topology_exceptions"] += 1
            if len(exception_samples) < 8:
                exception_samples.append(
                    {"stage": "topology", "type": type(error).__name__, "message": str(error)}
                )
            continue
        anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
        if not all(value >= 0 for value in anomaly):
            rejections["anomaly"] += 1
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
            rejections["slope"] += 1
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
            if len(exception_samples) < 8:
                exception_samples.append(
                    {
                        "stage": "cohomology",
                        "type": type(error).__name__,
                        "message": str(error),
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
            rejections["spectrum_or_quality"] += 1
            continue
        counters["spectrum_survivors"] += 1
        if not raw_q1_signature(cohomology):
            rejections["not_raw_q1"] += 1
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
                f"raw_q1={counters['raw_q1_spectrum_survivors']}",
                flush=True,
            )

    certified_records = []
    filtered_records = []
    representative_gate = RepresentativeGrammarGate()
    for index, raw in enumerate(raw_q1_records[:max_raw_q1_to_certify]):
        counters["raw_q1_certification_attempts"] += 1
        certified = certify_5259_matrix(
            label=f"radius6_broad_adjacency_certified_{index}",
            matrix=raw["matrix"],
            move=[raw["move"]],
            slope_restarts=certification_restarts,
            slope_seed=seed + 900000 + index,
        )
        certified["radius6_broad_source_id"] = raw["source_id"]
        certified["radius6_broad_source_status"] = raw["source_status"]
        certified["radius6_broad_move"] = raw["move"]
        if certified["character_certified"]:
            counters["character_certified_q1_survivors"] += 1
        certified_records.append(certified)
        filtered = candidate_certificate_from_5259_record(
            label=f"radius6_broad_adjacency_filtered_{index}",
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
        filtered["radius6_broad_source_id"] = raw["source_id"]
        filtered["radius6_broad_source_status"] = raw["source_status"]
        filtered["radius6_broad_move"] = raw["move"]
        apply_representative_grammar_boundary(
            filtered_record=filtered,
            grammar_gate=representative_gate,
            source={
                "kind": "active_broad_adjacency_scout",
                "source_radius": source_radius,
                "target_radius": source_radius + 1,
                "source_id": raw["source_id"],
                "source_status": raw["source_status"],
                "move": raw["move"],
            },
            weight=1,
        )
        filtered_records.append(filtered)

    categories = Counter(item["classification"]["category"] for item in filtered_records)
    statuses = Counter(item["classification"]["status"] for item in filtered_records)
    refined_statuses = Counter(
        item["character_refined_classification"]["status"] for item in filtered_records
    )
    representative_statuses = Counter(
        item["representative_grammar_gate"]["representative_grammar_stage"]["status"]
        for item in filtered_records
    )
    viable = [
        item
        for item in filtered_records
        if item["representative_grammar_gate"]["representative_grammar_stage"][
            "promoted_to_lead_candidate"
        ]
    ]
    cup_product_eligible = [
        item
        for item in filtered_records
        if item["representative_grammar_gate"]["representative_grammar_stage"][
            "cup_product_planning_allowed"
        ]
    ]
    gates = {
        "imports_verified_source_frontier": gate(
            source_metadata["verifications_pass"] and source_metadata["source_count"] > 0,
            ", ".join(source_metadata["verification_paths"]),
            "broad adjacency scout imports verified q1 source frontier artifacts",
        ),
        "screening_window_valid": gate(
            len(screened) > 0 or frontier_start >= len(frontier),
            "radius6 broad adjacency frontier",
            "the configured broad radius6 window is valid",
        ),
        "certification_budget_respected": gate(
            counters["raw_q1_certification_attempts"]
            == min(counters["raw_q1_spectrum_survivors"], max_raw_q1_to_certify),
            "radius6 broad raw q1 certification budget",
            "the certification pass attempted the configured number of raw q1 survivors",
        ),
        "representative_grammar_boundary_applied": gate(
            all("representative_grammar_gate" in item for item in filtered_records)
            and len(filtered_records) == sum(representative_statuses.values()),
            "representative grammar gate",
            "every emitted q1 candidate is classified at the representative grammar boundary",
        ),
    }
    return {
        "scope": (
            f"broad radius{source_radius + 1} adjacency scout from verified "
            f"radius{source_radius} q1 sources"
        ),
        "status": (
            "viable_candidate_found_in_radius6_broad_adjacency_scout"
            if viable
            else "no_viable_candidate_found_in_radius6_broad_adjacency_scout_window"
        ),
        "search_parameters": {
            "max_abs_charge_bound": max_abs_charge_bound,
            "frontier_start": frontier_start,
            "max_frontier_to_screen": max_frontier_to_screen,
            "max_raw_q1_to_certify": max_raw_q1_to_certify,
            "slope_restarts": slope_restarts,
            "slope_max_iterations": slope_max_iterations,
            "certification_restarts": certification_restarts,
            "seed": seed,
            "source_radius": source_radius,
            "target_radius": source_radius + 1,
        },
        "source_summary": source_metadata,
        "frontier_counters": frontier_counters,
        "screening_counters": counters,
        "rejection_counters": dict(sorted(rejections.items())),
        "summary": {
            "raw_q1_spectrum_survivors": counters["raw_q1_spectrum_survivors"],
            "certified_q1_records": len(filtered_records),
            "character_certified_q1_survivors": counters[
                "character_certified_q1_survivors"
            ],
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
            "character_refined_statuses": dict(sorted(refined_statuses.items())),
            "representative_grammar_statuses": dict(
                sorted(representative_statuses.items())
            ),
            "representative_grammar_promoted_count": len(viable),
            "cup_product_eligible_count": len(cup_product_eligible),
            "viable_count": len(viable),
        },
        "raw_q1_records": raw_q1_records,
        "certified_records": certified_records,
        "filtered_candidate_records": filtered_records,
        "exception_samples": exception_samples,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    target_radius = report["search_parameters"]["target_radius"]
    lines = [
        f"# Radius-{target_radius} Broad Adjacency Scout",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Screening", ""])
    for key, value in report["screening_counters"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Classifications", ""])
    for record in report["filtered_candidate_records"]:
        lines.append(
            f"- `{record['label']}` from `{record['radius6_broad_source_id']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-radius", type=int, default=5, choices=[5, 6, 7, 8])
    parser.add_argument("--max-abs-charge-bound", type=int, default=4)
    parser.add_argument("--frontier-start", type=int, default=0)
    parser.add_argument("--max-frontier-to-screen", type=int, default=2400)
    parser.add_argument("--max-raw-q1-to-certify", type=int, default=80)
    parser.add_argument("--slope-restarts", type=int, default=8)
    parser.add_argument("--slope-max-iterations", type=int, default=1500)
    parser.add_argument("--certification-restarts", type=int, default=32)
    parser.add_argument("--seed", type=int, default=626000)
    parser.add_argument("--progress-every", type=int, default=0)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_broad_adjacency_scout.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_broad_adjacency_scout.md"),
    )
    args = parser.parse_args()
    report = build_report(
        max_abs_charge_bound=args.max_abs_charge_bound,
        frontier_start=args.frontier_start,
        max_frontier_to_screen=args.max_frontier_to_screen,
        max_raw_q1_to_certify=args.max_raw_q1_to_certify,
        slope_restarts=args.slope_restarts,
        slope_max_iterations=args.slope_max_iterations,
        certification_restarts=args.certification_restarts,
        seed=args.seed,
        progress_every=args.progress_every,
        source_radius=args.source_radius,
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
