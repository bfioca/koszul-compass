#!/usr/bin/env python3
"""Summarize the current radius-2 q=1 frontier after rank-resolution work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def prediction_is_currently_desired_q1(prediction: dict[str, Any]) -> bool:
    return (
        prediction.get("regular_character_rule_applies")
        and prediction.get("net_families") == 3
        and prediction.get("colored_triplet_vectorlike_pairs") == 1
        and prediction.get("electroweak_doublet_vectorlike_pairs") == 1
    )


def build_report() -> dict[str, Any]:
    aggregate = load_json(REPORTS / "phenomenology_guided_q1_radius2_aggregate.json")
    unresolved_audit = load_json(REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.json")
    enhanced = load_json(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json")
    residual = load_json(REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json")
    rank_resolved = load_json(REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog.json")
    medium_scenarios_path = REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios.json"
    medium_scenarios = (
        load_json(medium_scenarios_path)
        if medium_scenarios_path.exists()
        else None
    )
    medium_rank_path = REPORTS / "phenomenology_guided_q1_radius2_medium_rank_resolved.json"
    medium_rank = load_json(medium_rank_path) if medium_rank_path.exists() else None

    medium_records = [
        record
        for record in residual["records"]
        if record["priority_bucket"] == "medium_priority_small_map_backlog"
    ]
    medium_current_q1 = [
        record
        for record in medium_records
        if prediction_is_currently_desired_q1(
            record["current_prediction_after_enhancement"]
        )
    ]
    high_rank_records = rank_resolved["filtered_candidate_records"]
    medium_new_obstructed = (
        medium_rank["summary"]["categories"]["phenomenologically obstructed"]
        if medium_rank is not None
        else 0
    )
    medium_remaining_unresolved = (
        medium_rank["summary"]["categories"]["unresolved"]
        if medium_rank is not None
        and "unresolved" in medium_rank["summary"]["categories"]
        else (0 if medium_rank is not None else len(medium_records))
    )
    current_obstructed_count = (
        aggregate["aggregate_categories"]["phenomenologically obstructed"]
        + 1  # unresolved-audit no-triplet record strengthened to obstructed
        + enhanced["summary"]["categories"]["phenomenologically obstructed"]
        + rank_resolved["summary"]["categories"]["phenomenologically obstructed"]
        + medium_new_obstructed
    )
    current_unresolved_count = medium_remaining_unresolved
    gates = {
        "aggregate_imported": gate(
            aggregate["aggregate_totals"]["raw_q1_spectrum_survivors"] == 29
            and aggregate["aggregate_totals"]["viable_count"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius2_aggregate.json"),
            "current frontier starts from the verified radius-2 q=1 aggregate",
        ),
        "high_priority_frontier_closed": gate(
            rank_resolved["summary"]["high_priority_records"] == 4
            and rank_resolved["summary"]["desired_q1_records"] == 4
            and rank_resolved["summary"]["viable_count"] == 0
            and rank_resolved["summary"]["remaining_unresolved_blocks"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog.json"),
            "all high-priority rank-scenario records are character-certified and obstructed",
        ),
        "medium_frontier_is_only_remaining_uncertainty": gate(
            len(medium_records) == 5
            and len(medium_current_q1) == 0
            and all(
                not prediction_is_currently_desired_q1(
                    record["current_prediction_after_enhancement"]
                )
                for record in medium_records
            ),
            str(REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json"),
            "remaining residual records are medium-priority and not currently desired-q1",
        ),
        "all_currently_certified_desired_q1_are_obstructed": gate(
            all(
                record["spectrum_certificate"]["desired_q1_three_family_signature"]
                and record["classification"]["status"]
                == "negative_control_doublet_triplet_obstruction"
                for record in high_rank_records
            ),
            str(REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog.json"),
            "newly certified desired-q1 records all fail the negative-control filter",
        ),
        "counts_are_accounted": gate(
            current_obstructed_count == 29
            and current_unresolved_count == 0
            and current_obstructed_count + current_unresolved_count == 29,
            "current frontier count accounting",
            "all 29 radius-2 q=1 attempts are either obstructed or in the remaining medium backlog",
        ),
        "medium_scenarios_imported_if_available": gate(
            medium_scenarios is not None
            and medium_scenarios["summary"]["medium_records"] == 5
            and medium_scenarios["summary"]["two_term_supported_records"] == 3
            and medium_scenarios["summary"]["unsupported_three_term_records"] == 2,
            str(medium_scenarios_path),
            "current frontier imports the medium-priority scenario refinement",
        ),
        "medium_rank_resolution_imported_if_available": gate(
            medium_rank is not None
            and medium_rank["summary"]["desired_q1_records"] == 4
            and medium_rank["summary"]["viable_count"] == 0
            and medium_rank["summary"]["categories"] == {"phenomenologically obstructed": 5},
            str(medium_rank_path),
            "current frontier imports the medium rank-resolved classifications",
        ),
    }
    return {
        "scope": "current radius-2 q=1 frontier after enhanced and rank-resolved character certification",
        "status": "no_viable_candidate_found_high_priority_frontier_closed",
        "summary": {
            "raw_q1_spectrum_survivors": aggregate["aggregate_totals"]["raw_q1_spectrum_survivors"],
            "current_obstructed_count": current_obstructed_count,
            "current_unresolved_count": current_unresolved_count,
            "viable_count": 0,
            "high_priority_rank_resolved_desired_q1": rank_resolved["summary"]["desired_q1_records"],
            "high_priority_rank_resolved_obstructed": rank_resolved["summary"]["categories"]["phenomenologically obstructed"],
            "remaining_medium_records": len(medium_records),
            "remaining_medium_currently_desired_q1": len(medium_current_q1),
            "remaining_medium_two_term_supported_records": (
                medium_scenarios["summary"]["two_term_supported_records"]
                if medium_scenarios is not None
                else None
            ),
            "remaining_medium_unsupported_three_term_records": (
                medium_scenarios["summary"]["unsupported_three_term_records"]
                if medium_scenarios is not None
                else None
            ),
            "remaining_medium_desired_q1_rank_scenarios": (
                medium_scenarios["summary"]["total_desired_q1_scenarios"]
                if medium_scenarios is not None
                else None
            ),
            "medium_rank_resolved_desired_q1": (
                medium_rank["summary"]["desired_q1_records"]
                if medium_rank is not None
                else None
            ),
            "medium_rank_resolved_obstructed": medium_new_obstructed,
            "medium_rank_resolved_remaining_unresolved": medium_remaining_unresolved,
        },
        "high_priority_closure": {
            "source": "phenomenology_guided_q1_radius2_rank_resolved_backlog.json",
            "candidate_labels": [
                record["label"] for record in high_rank_records
            ],
            "classification_statuses": {
                record["label"]: record["classification"]["status"]
                for record in high_rank_records
            },
        },
        "remaining_medium_frontier": [
            {
                "label": record["label"],
                "source_window": record["source_window"],
                "source_filtered_label": record["source_filtered_label"],
                "current_prediction_after_enhancement": record[
                    "current_prediction_after_enhancement"
                ],
                "unresolved_blocks": record["unresolved_blocks"],
                "trace_feasible_for_q1": record["trace_feasibility"][
                    "desired_q1_trace_feasible"
                ],
                "trace_feasibility": record["trace_feasibility"],
            }
            for record in medium_records
        ],
        "interpretation": (
            "The high-priority branch and the medium branch have both been character-certified. "
            "All 29 radius-2 q=1 attempts are now classified, no viable candidate survives, "
            "and every certified desired-q1 survivor is rejected by the phenomenology filter."
        ),
        "medium_scenario_refinement": medium_scenarios["summary"]
        if medium_scenarios is not None
        else None,
        "medium_rank_resolution": medium_rank["summary"]
        if medium_rank is not None
        else None,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Current Q1 Frontier",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    if report["summary"]["current_unresolved_count"]:
        lines.extend(["## Remaining Medium Frontier", ""])
        for record in report["remaining_medium_frontier"]:
            lines.append(
                "- "
                f"`{record['label']}` from `{record['source_window']}/{record['source_filtered_label']}`: "
                f"prediction `{record['current_prediction_after_enhancement']}`; "
                f"blocks `{len(record['unresolved_blocks'])}`; "
                f"trace-feasible q1 `{record['trace_feasible_for_q1']}`"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_current_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_current_frontier.md"),
    )
    args = parser.parse_args()
    report = build_report()
    Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, Path(args.md_out))
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
