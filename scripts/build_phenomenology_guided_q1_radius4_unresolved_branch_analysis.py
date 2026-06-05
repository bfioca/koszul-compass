#!/usr/bin/env python3
"""Bounded branch analysis for remaining selected radius-4 unresolved records."""

from __future__ import annotations

import argparse
import copy
import itertools
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import (  # noqa: E402
    representation_record,
    sector_record,
)
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def possible_actuals_for_cohomology(cohomology: list[int]) -> list[dict[str, Any]]:
    degree_options = []
    for degree, dimension in enumerate(cohomology):
        if dimension == 0:
            continue
        traces = list(range(-dimension, dimension + 1, 2))
        degree_options.append(
            [
                (f"H{degree}", representation_record(dimension, trace))
                for trace in traces
            ]
        )
    actuals = []
    for combo in itertools.product(*degree_options):
        actuals.append({key: rep for key, rep in combo})
    return actuals


def unresolved_certs(characters: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = []
    for sector_key, sector in characters.items():
        for cert_index, cert in enumerate(sector["line_certificates"]):
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            blocks.append(
                {
                    "sector_key": sector_key,
                    "cert_index": cert_index,
                    "summand_index": cert.get("summand_index"),
                    "summand_pair": cert.get("summand_pair"),
                    "line_bundle": cert["line_bundle"],
                    "cohomology": cert["cohomology"],
                    "actual_options": possible_actuals_for_cohomology(
                        cert["cohomology"]
                    ),
                }
            )
    return blocks


def complete_characters_with_branch(
    characters: dict[str, Any],
    blocks: list[dict[str, Any]],
    branch_actuals: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    completed = copy.deepcopy(characters)
    for block, actual in zip(blocks, branch_actuals):
        cert = completed[block["sector_key"]]["line_certificates"][block["cert_index"]]
        cert["actual"] = copy.deepcopy(actual)
        cert["method"] = "radius4_dimension_compatible_branch_completion"
        cert["actual_character_computed"] = True
    for sector_key, target_keys in SECTOR_TARGET_KEYS.items():
        sector = completed[sector_key]
        completed[sector_key] = sector_record(
            label=SECTOR_LABELS[sector_key],
            line_certificates=sector["line_certificates"],
            cohomology_degree_keys=target_keys,
        )
    return completed


def branch_space_size(blocks: list[dict[str, Any]]) -> int:
    total = 1
    for block in blocks:
        total *= len(block["actual_options"])
    return total


def build_report(*, max_branches_per_record: int) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    current = load_json(REPORTS / "phenomenology_guided_q1_radius4_current_frontier.json")
    known = load_json(REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    unresolved_records = [
        record
        for record in known["resolved_records"]
        if not record["character_certified"]
    ]
    branch_reports = []
    all_branch_certificates = []
    skipped = []
    for record in unresolved_records:
        blocks = unresolved_certs(record["characters"])
        size = branch_space_size(blocks)
        block_summary = [
            {
                "sector": block["sector_key"],
                "summand_index": block["summand_index"],
                "summand_pair": block["summand_pair"],
                "line_bundle": block["line_bundle"],
                "cohomology": block["cohomology"],
                "option_count": len(block["actual_options"]),
            }
            for block in blocks
        ]
        if size > max_branches_per_record:
            skipped.append(
                {
                    "label": f"{record['source_window']}/{record['source_filtered_label']}",
                    "branch_space_size": size,
                    "unresolved_blocks": block_summary,
                    "reason": "branch_space_exceeds_configured_bound",
                }
            )
            branch_reports.append(
                {
                    "label": f"{record['source_window']}/{record['source_filtered_label']}",
                    "branch_space_size": size,
                    "branches_evaluated": 0,
                    "skipped": True,
                    "unresolved_blocks": block_summary,
                }
            )
            continue
        branches = []
        categories: Counter[str] = Counter()
        statuses: Counter[str] = Counter()
        desired_count = 0
        viable_count = 0
        option_lists = [block["actual_options"] for block in blocks]
        for branch_index, branch_actuals in enumerate(itertools.product(*option_lists)):
            completed_characters = complete_characters_with_branch(
                record["characters"], blocks, branch_actuals
            )
            completed = copy.deepcopy(record)
            completed["characters"] = completed_characters
            completed["character_certified"] = True
            completed["vectorlike_pair_prediction"] = prediction_from_characters(
                completed_characters
            )
            completed["radius4_unresolved_branch_completion"] = {
                "branch_index": branch_index,
                "filled_blocks": [
                    {
                        "sector": block["sector_key"],
                        "summand_index": block["summand_index"],
                        "summand_pair": block["summand_pair"],
                        "line_bundle": block["line_bundle"],
                        "actual": actual,
                    }
                    for block, actual in zip(blocks, branch_actuals)
                ],
            }
            filtered = candidate_certificate_from_5259_record(
                label=(
                    f"{record['source_window']}_{record['source_filtered_label']}"
                    f"_branch_{branch_index}"
                ),
                record=completed,
                conf=conf,
            )
            filtered["source_window"] = record["source_window"]
            filtered["source_filtered_label"] = record["source_filtered_label"]
            filtered["radius4_unresolved_branch_completion"] = completed[
                "radius4_unresolved_branch_completion"
            ]
            apply_monoid_obstruction_override(filtered)
            categories[filtered["classification"]["category"]] += 1
            statuses[filtered["classification"]["status"]] += 1
            if filtered["spectrum_certificate"]["desired_q1_three_family_signature"]:
                desired_count += 1
            if filtered["classification"]["category"] == "viable":
                viable_count += 1
            branches.append(
                {
                    "label": filtered["label"],
                    "prediction": filtered["spectrum_certificate"][
                        "vectorlike_prediction"
                    ],
                    "desired_q1": filtered["spectrum_certificate"][
                        "desired_q1_three_family_signature"
                    ],
                    "classification": filtered["classification"],
                }
            )
            all_branch_certificates.append(filtered)
        branch_reports.append(
            {
                "label": f"{record['source_window']}/{record['source_filtered_label']}",
                "branch_space_size": size,
                "branches_evaluated": len(branches),
                "skipped": False,
                "unresolved_blocks": block_summary,
                "desired_q1_branches": desired_count,
                "viable_branches": viable_count,
                "categories": dict(sorted(categories.items())),
                "statuses": dict(sorted(statuses.items())),
                "branches": branches,
            }
        )

    aggregate_categories = Counter(
        branch["classification"]["category"] for branch in all_branch_certificates
    )
    aggregate_statuses = Counter(
        branch["classification"]["status"] for branch in all_branch_certificates
    )
    gates = {
        "imports_current_frontier": gate(
            current["all_gates_pass"]
            and current["summary"]["current_unresolved_count"] == 14,
            str(REPORTS / "phenomenology_guided_q1_radius4_current_frontier.json"),
            "branch analysis starts from the verified 14-record unresolved frontier",
        ),
        "attempts_all_unresolved_records": gate(
            len(unresolved_records) == len(branch_reports) == 14,
            str(REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json"),
            "every remaining unresolved radius-4 record is included",
        ),
        "bounded_records_evaluated": gate(
            sum(1 for item in branch_reports if not item["skipped"]) > 0
            and all(
                item["branch_space_size"] <= max_branches_per_record
                for item in branch_reports
                if not item["skipped"]
            ),
            "dimension-compatible branch enumeration",
            "all evaluated records respect the configured branch bound",
        ),
        "no_viable_branch_found": gate(
            all(
                item.get("viable_branches", 0) == 0
                for item in branch_reports
                if not item["skipped"]
            ),
            "dimension-compatible branch classifications",
            "no evaluated dimension-compatible branch passes the charge-level filter",
        ),
    }
    return {
        "scope": "bounded dimension-compatible branch analysis for selected radius-4 unresolved records",
        "status": "no_viable_branch_found_in_bounded_radius4_unresolved_branch_analysis",
        "parameters": {"max_branches_per_record": max_branches_per_record},
        "summary": {
            "unresolved_records": len(unresolved_records),
            "records_evaluated": sum(1 for item in branch_reports if not item["skipped"]),
            "records_skipped": len(skipped),
            "branches_evaluated": len(all_branch_certificates),
            "desired_q1_branches": sum(
                1
                for branch in all_branch_certificates
                if branch["spectrum_certificate"]["desired_q1_three_family_signature"]
            ),
            "viable_branches": sum(
                1
                for branch in all_branch_certificates
                if branch["classification"]["category"] == "viable"
            ),
            "categories": dict(sorted(aggregate_categories.items())),
            "statuses": dict(sorted(aggregate_statuses.items())),
        },
        "record_branch_reports": branch_reports,
        "skipped_records": skipped,
        "branch_candidate_records": all_branch_certificates,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Unresolved Branch Analysis",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Records", ""])
    for item in report["record_branch_reports"]:
        if item["skipped"]:
            lines.append(
                f"- `{item['label']}` skipped; branch space `{item['branch_space_size']}`"
            )
        else:
            lines.append(
                f"- `{item['label']}`: branches `{item['branches_evaluated']}`, "
                f"desired-q1 `{item['desired_q1_branches']}`, "
                f"viable `{item['viable_branches']}`, statuses `{item['statuses']}`"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This is a dimension-compatible branch audit, not a replacement for "
                "explicit map-rank character computation. It identifies which "
                "remaining unresolved records can be rejected for every bounded "
                "character completion and which still require new line-level probes."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-branches-per-record", type=int, default=128)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis.md"),
    )
    args = parser.parse_args()
    report = build_report(max_branches_per_record=args.max_branches_per_record)
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
