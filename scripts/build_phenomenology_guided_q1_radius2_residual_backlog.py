#!/usr/bin/env python3
"""Prioritize the residual enhanced radius-2 q=1 character backlog."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WEDGE_TARGETS = {
    ("wedge2_V", "H1"): {"dimension": 8, "regular_multiplicity": 4},
    ("wedge2_V", "H2"): {"dimension": 2, "regular_multiplicity": 1},
    ("wedge2_V_dual", "H1"): {"dimension": 2, "regular_multiplicity": 1},
    ("wedge2_V_dual", "H2"): {"dimension": 8, "regular_multiplicity": 4},
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def trace_zero_feasible(*, partial_trace: int, missing_dimension: int) -> bool:
    required_trace = -partial_trace
    return (
        missing_dimension >= 0
        and abs(required_trace) <= missing_dimension
        and (missing_dimension + required_trace) % 2 == 0
    )


def target_trace_feasibility(record: dict[str, Any]) -> dict[str, Any]:
    characters = record["characters"]
    targets = {}
    all_feasible = True
    for (sector, key), expected in WEDGE_TARGETS.items():
        partial = characters[sector]["cohomology_characters"][key]
        missing_dimension = expected["dimension"] - partial["dimension"]
        feasible = trace_zero_feasible(
            partial_trace=partial["nonidentity_trace"],
            missing_dimension=missing_dimension,
        )
        all_feasible = all_feasible and feasible
        targets[f"{sector}.{key}"] = {
            "target_dimension": expected["dimension"],
            "target_regular_multiplicity": expected["regular_multiplicity"],
            "partial_dimension": partial["dimension"],
            "partial_trace": partial["nonidentity_trace"],
            "missing_dimension": missing_dimension,
            "required_missing_trace_for_regular": -partial["nonidentity_trace"],
            "trace_zero_feasible": feasible,
        }
    return {
        "desired_q1_trace_feasible": all_feasible,
        "targets": targets,
    }


def residual_complexity(record: dict[str, Any]) -> dict[str, Any]:
    reasons = Counter(block["reason"] for block in record["enhancement"]["unresolved_blocks"])
    source_degree_widths = []
    total_source_dimensions = []
    for block in record["enhancement"]["unresolved_blocks"]:
        degrees = [int(degree) for degree in block["source_total_dimensions"]]
        source_degree_widths.append(max(degrees) - min(degrees) + 1)
        total_source_dimensions.append(sum(block["source_total_dimensions"].values()))
    return {
        "unresolved_block_count": record["enhancement"]["unresolved_block_count"],
        "reason_counts": dict(sorted(reasons.items())),
        "max_source_degree_width": max(source_degree_widths, default=0),
        "total_source_dimension": sum(total_source_dimensions),
    }


def priority_bucket(record: dict[str, Any], feasibility: dict[str, Any], complexity: dict[str, Any]) -> str:
    prediction = record["vectorlike_pair_prediction"]
    if not feasibility["desired_q1_trace_feasible"]:
        return "trace_infeasible_low_priority"
    if prediction["net_families"] == 3 and prediction["colored_triplet_vectorlike_pairs"] in {0, 1}:
        return "high_priority_q1_or_adjacent"
    if prediction["net_families"] == 3:
        return "medium_priority_three_family"
    if complexity["unresolved_block_count"] <= 2:
        return "medium_priority_small_map_backlog"
    return "low_priority_nonq1_or_large_map_backlog"


def build_report() -> dict[str, Any]:
    enhanced = load_json(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json")
    residual_records = [
        record
        for record in enhanced["enhanced_records"]
        if not record["character_certified"]
    ]
    records = []
    buckets = Counter()
    reasons = Counter()
    for record in residual_records:
        feasibility = target_trace_feasibility(record)
        complexity = residual_complexity(record)
        bucket = priority_bucket(record, feasibility, complexity)
        buckets[bucket] += 1
        reasons.update(complexity["reason_counts"])
        records.append(
            {
                "label": record["label"],
                "source_window": record["source_window"],
                "source_filtered_label": record["source_filtered_label"],
                "matrix": record["matrix"],
                "current_prediction_after_enhancement": record[
                    "vectorlike_pair_prediction"
                ],
                "trace_feasibility": feasibility,
                "complexity": complexity,
                "priority_bucket": bucket,
                "unresolved_blocks": record["enhancement"]["unresolved_blocks"],
            }
        )
    records.sort(
        key=lambda item: (
            {
                "high_priority_q1_or_adjacent": 0,
                "medium_priority_three_family": 1,
                "medium_priority_small_map_backlog": 2,
                "low_priority_nonq1_or_large_map_backlog": 3,
                "trace_infeasible_low_priority": 4,
            }[item["priority_bucket"]],
            item["complexity"]["unresolved_block_count"],
            item["complexity"]["total_source_dimension"],
            item["label"],
        )
    )
    gates = {
        "imports_enhanced_backlog": gate(
            enhanced["summary"]["remaining_unresolved_block_count"] == 18
            and enhanced["summary"]["statuses"][
                "enhanced_character_certificate_still_incomplete"
            ]
            == 9,
            str(REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json"),
            "residual report starts from the verified enhanced character backlog",
        ),
        "all_residual_records_ranked": gate(
            len(records) == 9
            and sum(item["complexity"]["unresolved_block_count"] for item in records)
            == 18,
            "enhanced residual records",
            "all nine incomplete records and eighteen remaining blocks are included",
        ),
        "residual_reason_taxonomy_matches": gate(
            dict(sorted(reasons.items()))
            == {"not_single_nonzero_cohomology_degree": 14, "not_two_term": 4},
            "enhanced residual blocks",
            "remaining blocks split into mixed two-degree and three-term map cases",
        ),
        "trace_feasibility_recorded": gate(
            all(item["trace_feasibility"]["desired_q1_trace_feasible"] for item in records),
            "partial wedge-sector character traces",
            "all residual records remain trace-feasible for the desired q=1 regular wedge signature",
        ),
    }
    return {
        "scope": "residual character-map backlog prioritization after two-term enhancement",
        "status": "residual_backlog_prioritized",
        "summary": {
            "residual_records": len(records),
            "residual_blocks": sum(
                item["complexity"]["unresolved_block_count"] for item in records
            ),
            "priority_buckets": dict(sorted(buckets.items())),
            "reason_counts": dict(sorted(reasons.items())),
            "all_trace_feasible_for_q1": all(
                item["trace_feasibility"]["desired_q1_trace_feasible"]
                for item in records
            ),
        },
        "records": records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 Residual Character Backlog",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- residual records: `{report['summary']['residual_records']}`",
        f"- residual blocks: `{report['summary']['residual_blocks']}`",
        f"- priority buckets: `{report['summary']['priority_buckets']}`",
        f"- reason counts: `{report['summary']['reason_counts']}`",
        f"- all trace-feasible for q=1: `{report['summary']['all_trace_feasible_for_q1']}`",
        "",
        "## Ranked Records",
        "",
    ]
    for item in report["records"]:
        lines.append(
            "- "
            f"`{item['label']}` from `{item['source_window']}/{item['source_filtered_label']}`: "
            f"`{item['priority_bucket']}`, "
            f"prediction `{item['current_prediction_after_enhancement']}`, "
            f"blocks `{item['complexity']['unresolved_block_count']}`, "
            f"source dimension `{item['complexity']['total_source_dimension']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The residual uncertainty is localized to equivariant map characters "
                "for mixed wedge-sector cohomology blocks. The existing partial traces "
                "do not rule out the desired q=1 regular wedge signature for any "
                "residual record, so closing this frontier requires map-level character "
                "data rather than another scalar dimension-only shortcut."
            ),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"residual_records={report['summary']['residual_records']}")
    print(f"residual_blocks={report['summary']['residual_blocks']}")
    print(f"priority_buckets={report['summary']['priority_buckets']}")
    print(f"reason_counts={report['summary']['reason_counts']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
