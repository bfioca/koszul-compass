#!/usr/bin/env python3
"""Combine known-line-resolved radius-4 batches into one frontier ledger."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

BATCHES = [
    {
        "batch": "batch1",
        "report": REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json",
        "verification": REPORTS
        / "phenomenology_guided_q1_radius4_known_line_resolved_verification.json",
    },
    {
        "batch": "batch2",
        "report": REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json",
        "verification": REPORTS
        / "phenomenology_guided_q1_radius4_batch2_known_line_resolved_verification.json",
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def has_required_sections(record: dict[str, Any]) -> bool:
    return {
        "spectrum_certificate",
        "character_certificate",
        "mass_operator_table",
        "proton_decay_operator_table",
        "classification",
    }.issubset(record)


def build_report() -> dict[str, Any]:
    reports = []
    verifications = []
    for batch in BATCHES:
        report = load_json(batch["report"])
        verification = load_json(batch["verification"])
        reports.append(report)
        verifications.append(verification)

    records = [
        record
        for report in reports
        for record in report["filtered_candidate_records"]
    ]
    character_certified = [
        record
        for record in records
        if record["character_certificate"]["character_certified"]
    ]
    viable = [
        record
        for record in records
        if record["classification"]["category"] == "viable"
    ]
    categories = Counter(record["classification"]["category"] for record in records)
    statuses = Counter(record["classification"]["status"] for record in records)

    per_batch = []
    for batch, report, verification in zip(BATCHES, reports, verifications):
        per_batch.append(
            {
                "batch": batch["batch"],
                "report": str(batch["report"]),
                "verification": str(batch["verification"]),
                "verification_passed": verification["all_gates_pass"],
                "summary": report["summary"],
                "status": report["status"],
            }
        )

    gates = {
        "all_source_verifications_pass": gate(
            all(item["all_gates_pass"] for item in verifications),
            ", ".join(str(batch["verification"]) for batch in BATCHES),
            "combined frontier imports only verified known-line reports",
        ),
        "all_builder_gates_pass": gate(
            all(report["all_gates_pass"] for report in reports),
            ", ".join(str(batch["report"]) for batch in BATCHES),
            "builder gates passed for every known-line-resolved batch",
        ),
        "record_count_matches_batch_summaries": gate(
            len(records)
            == sum(report["summary"]["attempted_unresolved_records"] for report in reports)
            == 45,
            "known-line-resolved filtered_candidate_records",
            "combined record count matches batch summaries",
        ),
        "required_sections_present": gate(
            all(has_required_sections(record) for record in records),
            "combined filtered candidate records",
            "every combined candidate emits the required deliverable sections",
        ),
        "classified_records_match_summary": gate(
            dict(sorted(categories.items()))
            == {"phenomenologically obstructed": 17, "unresolved": 28}
            and dict(sorted(statuses.items()))
            == {
                "known_line_resolution_still_incomplete": 27,
                "negative_control_doublet_triplet_obstruction": 16,
                "no_certified_triplet_mass_operator_found": 1,
                "no_triplet_mass_in_certified_singlet_monoid": 1,
            },
            "combined classifications",
            "combined classifications preserve exact batch-1 and batch-2 counts",
        ),
        "no_viable_candidate_found": gate(
            len(viable) == 0,
            "combined classifications",
            "no selected radius-4 known-line-resolved candidate passes the charge-level filter",
        ),
    }

    return {
        "scope": "combined known-line-resolved selected radius-4 frontier",
        "status": "viable_candidate_found_in_combined_known_line_frontier"
        if viable
        else "no_viable_candidate_found_in_combined_known_line_frontier",
        "per_batch": per_batch,
        "summary": {
            "batches": [batch["batch"] for batch in BATCHES],
            "attempted_unresolved_records": len(records),
            "filled_blocks": sum(report["summary"]["filled_blocks"] for report in reports),
            "remaining_unresolved_blocks": sum(
                report["summary"]["remaining_unresolved_blocks"] for report in reports
            ),
            "incompatible_known_actuals": sum(
                report["summary"]["incompatible_known_actuals"] for report in reports
            ),
            "character_certified_records": len(character_certified),
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Combined Radius-4 Known-Line Frontier",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Batches", ""])
    for batch in report["per_batch"]:
        lines.append(
            "- "
            f"`{batch['batch']}`: `{batch['status']}`; "
            f"verified `{batch['verification_passed']}`; "
            f"attempted `{batch['summary']['attempted_unresolved_records']}`; "
            f"certified `{batch['summary']['character_certified_records']}`; "
            f"viable `{batch['summary']['viable_count']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "Across the first two selected radius-4 source batches, known-line "
                "resolution turns additional q=1 spectrum survivors into charge-level "
                "classifications. The 5259-derived filter rejects every fully viable "
                "candidate found so far; the remaining frontier is limited to "
                "incomplete character data or mass-operator uncertainty."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_known_line_combined_frontier.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_known_line_combined_frontier.md"
        ),
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
