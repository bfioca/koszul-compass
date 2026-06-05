#!/usr/bin/env python3
"""Build the bounded radius-3 obstruction certificate ledger."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

WINDOW_REPORTS = {
    "window1": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout.json",
    "window2": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window2.json",
    "window3": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window3.json",
    "window4": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window4.json",
}

RESOLUTION_REPORTS = [
    REPORTS / "phenomenology_guided_q1_radius3_high_priority_rank_resolved.json",
    REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_rank_resolved.json",
    REPORTS / "phenomenology_guided_q1_radius3_medium_small_rank_resolved.json",
    REPORTS / "phenomenology_guided_q1_radius3_low_repeated_rank_resolved.json",
    REPORTS / "phenomenology_guided_q1_radius3_low_remaining_rank_resolved.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def candidate_key(window: str | None, label: str | None) -> str:
    return f"{window}/{label}"


def required_sections(record: dict[str, Any]) -> bool:
    return {
        "spectrum_certificate",
        "character_certificate",
        "mass_operator_table",
        "proton_decay_operator_table",
        "classification",
    }.issubset(record)


def base_records() -> dict[str, dict[str, Any]]:
    records = {}
    for window, path in WINDOW_REPORTS.items():
        report = load_json(path)
        for record in report["filtered_candidate_records"]:
            item = copy.deepcopy(record)
            item["final_source_report"] = str(path)
            item["final_source_kind"] = "radius3_window_filter"
            item["source_window"] = window
            item["source_filtered_label"] = record["label"]
            records[candidate_key(window, record["label"])] = item
    return records


def apply_audit_strengthening(records: dict[str, dict[str, Any]]) -> int:
    audit = load_json(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json")
    count = 0
    for item in audit["records"]:
        audit_info = item["audit"]
        if audit_info.get("kind") != "certified_record_without_triplet_mass":
            continue
        if audit_info["recommended_classification"] != "phenomenologically obstructed":
            continue
        key = candidate_key(item["window"], item["label"])
        records[key]["classification"] = {
            "category": "phenomenologically obstructed",
            "status": audit_info["recommended_status"],
            "reason": "unresolved audit proved certified singlet monoid obstruction for triplet mass terms",
        }
        records[key]["radius3_unresolved_audit_override"] = audit_info
        records[key]["final_source_report"] = str(
            REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"
        )
        records[key]["final_source_kind"] = "audit_strengthened_obstruction"
        count += 1
    return count


def apply_resolution_reports(records: dict[str, dict[str, Any]]) -> int:
    count = 0
    for path in RESOLUTION_REPORTS:
        report = load_json(path)
        for record in report["filtered_candidate_records"]:
            key = candidate_key(record.get("source_window"), record.get("source_filtered_label"))
            item = copy.deepcopy(record)
            item["final_source_report"] = str(path)
            item["final_source_kind"] = "rank_resolved_filter"
            records[key] = item
            count += 1
    return count


def build_report() -> dict[str, Any]:
    aggregate = load_json(REPORTS / "phenomenology_guided_q1_radius3_adjacency_aggregate.json")
    frontier = load_json(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json")
    sign_conflict = load_json(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.json")
    sign_branches = load_json(
        REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis.json"
    )
    records = base_records()
    audit_overrides = apply_audit_strengthening(records)
    resolution_replacements = apply_resolution_reports(records)
    final_records = list(records.values())
    categories: dict[str, int] = {}
    statuses: dict[str, int] = {}
    source_kinds: dict[str, int] = {}
    desired_q1_count = 0
    viable_count = 0
    unresolved_records = []
    for record in final_records:
        category = record["classification"]["category"]
        status = record["classification"]["status"]
        categories[category] = categories.get(category, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1
        source_kinds[record["final_source_kind"]] = source_kinds.get(record["final_source_kind"], 0) + 1
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]:
            desired_q1_count += 1
        if category == "viable":
            viable_count += 1
        if category == "unresolved":
            unresolved_records.append(
                {
                    "key": candidate_key(
                        record.get("source_window"), record.get("source_filtered_label")
                    ),
                    "status": status,
                    "reason": record["classification"]["reason"],
                    "vectorlike_prediction": record["spectrum_certificate"][
                        "vectorlike_prediction"
                    ],
                }
            )
    gates = {
        "imports_current_frontier": gate(
            frontier["all_gates_pass"]
            and frontier["summary"]["current_obstructed_count"] == 63
            and frontier["summary"]["current_unresolved_count"] == 1
            and frontier["summary"]["viable_count"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json"),
            "certificate imports the verified current radius-3 frontier",
        ),
        "all_raw_q1_records_accounted": gate(
            len(final_records) == aggregate["aggregate_totals"]["raw_q1_spectrum_survivors"] == 64,
            "final radius-3 candidate ledger",
            "all 64 raw q=1 spectrum survivors have a final ledger record",
        ),
        "every_record_has_required_sections": gate(
            all(required_sections(record) for record in final_records),
            "final radius-3 candidate ledger",
            "every final record has spectrum, character, mass, proton, and classification sections",
        ),
        "final_counts_match_frontier": gate(
            categories == {"phenomenologically obstructed": 63, "unresolved": 1}
            and viable_count == 0,
            "final radius-3 candidate ledger",
            "final ledger counts match the current frontier counts",
        ),
        "only_unresolved_is_sign_conflict": gate(
            len(unresolved_records) == 1
            and unresolved_records[0]["key"] == "window2/radius3_adjacency_filtered_16"
            and sign_conflict["all_gates_pass"]
            and sign_conflict["status"] == "character_certificate_blocked_by_sign_constraint_conflict",
            str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.json"),
            "the only remaining unresolved candidate is the recorded sign-conflict character case",
        ),
        "sign_conflict_branches_nonviable": gate(
            sign_branches["all_gates_pass"]
            and sign_branches["status"] == "sign_conflict_branches_nonviable_under_current_filter"
            and all(
                record["classification"]["category"] != "viable"
                for record in sign_branches["branch_certificates"]
            ),
            str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis.json"),
            "both dimension-compatible branches of the sign-conflict record are nonviable",
        ),
    }
    return {
        "scope": "bounded radius-3 quotient-compatible q=1 obstruction certificate",
        "status": "no_viable_candidate_found_radius3_bounded_frontier_one_character_conflict",
        "summary": {
            "raw_q1_spectrum_survivors": len(final_records),
            "desired_q1_records_after_resolution": desired_q1_count,
            "phenomenologically_obstructed": categories.get("phenomenologically obstructed", 0),
            "unresolved": categories.get("unresolved", 0),
            "viable": viable_count,
            "sign_conflict_branches_checked": len(sign_branches["branch_certificates"]),
            "sign_conflict_viable_branches": sum(
                1
                for record in sign_branches["branch_certificates"]
                if record["classification"]["category"] == "viable"
            ),
            "audit_overrides": audit_overrides,
            "resolution_replacements": resolution_replacements,
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
            "source_kinds": dict(sorted(source_kinds.items())),
        },
        "unresolved_records": unresolved_records,
        "sign_conflict_branch_summary": [
            {
                "label": record["label"],
                "desired_q1": record["spectrum_certificate"][
                    "desired_q1_three_family_signature"
                ],
                "classification": record["classification"],
                "vectorlike_prediction": record["spectrum_certificate"][
                    "vectorlike_prediction"
                ],
            }
            for record in sign_branches["branch_certificates"]
        ],
        "final_candidate_records": final_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Bounded Obstruction Certificate",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Remaining Unresolved", ""])
    for record in report["unresolved_records"]:
        lines.append(
            f"- `{record['key']}`: `{record['status']}`; prediction `{record['vectorlike_prediction']}`"
        )
    lines.extend(["", "## Sign-Conflict Branches", ""])
    for record in report["sign_conflict_branch_summary"]:
        lines.append(
            "- "
            f"`{record['label']}`: desired_q1 `{record['desired_q1']}`, "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The bounded radius-3 frontier has no viable candidate under the current "
                "charge-level filter. All but one raw q=1 spectrum survivor are classified; "
                "the sole strict-ledger exception is the explicitly recorded sign-conflict "
                "character case. Its two dimension-compatible character branches are also "
                "nonviable under the same filter."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_bounded_obstruction_certificate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_bounded_obstruction_certificate.md"),
    )
    args = parser.parse_args()
    report = build_report()
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
