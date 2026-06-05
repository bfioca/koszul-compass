#!/usr/bin/env python3
"""Verify the residual enhanced radius-2 character-backlog prioritization."""

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


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_residual_backlog.md"
    enhanced_path = REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json"
    report = load_json(path)
    enhanced = load_json(enhanced_path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["records"]
    high_priority = [
        record
        for record in records
        if record["priority_bucket"] == "high_priority_q1_or_adjacent"
    ]
    mixed_blocks = [
        block
        for record in records
        for block in record["unresolved_blocks"]
        if block["reason"] == "not_single_nonzero_cohomology_degree"
    ]
    three_term_blocks = [
        block
        for record in records
        for block in record["unresolved_blocks"]
        if block["reason"] == "not_two_term"
    ]

    verification_gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "residual backlog builder gates pass",
        ),
        "imports_enhanced_residue": gate(
            enhanced["summary"]["statuses"]["enhanced_character_certificate_still_incomplete"]
            == 9
            and enhanced["summary"]["remaining_unresolved_block_count"] == 18
            and report["summary"]["residual_records"] == 9
            and report["summary"]["residual_blocks"] == 18
            and len(records) == 9,
            f"{enhanced_path}, {path}",
            "residual report imports the nine incomplete enhanced records and eighteen blocks",
        ),
        "reason_taxonomy_matches": gate(
            report["summary"]["reason_counts"]
            == {"not_single_nonzero_cohomology_degree": 14, "not_two_term": 4}
            and len(mixed_blocks) == 14
            and len(three_term_blocks) == 4,
            str(path),
            "remaining blocks are mixed two-degree or three-term equivariant map cases",
        ),
        "priority_buckets_match": gate(
            report["summary"]["priority_buckets"]
            == {"high_priority_q1_or_adjacent": 4, "medium_priority_small_map_backlog": 5}
            and len(high_priority) == 4
            and all(
                record["current_prediction_after_enhancement"]["net_families"] == 3
                and record["complexity"]["unresolved_block_count"] == 2
                for record in high_priority
            ),
            str(path),
            "four top-priority records are three-family q=1-adjacent two-block map cases",
        ),
        "trace_feasibility_matches": gate(
            report["summary"]["all_trace_feasible_for_q1"] is True
            and all(
                record["trace_feasibility"]["desired_q1_trace_feasible"]
                and all(
                    target["trace_zero_feasible"]
                    for target in record["trace_feasibility"]["targets"].values()
                )
                for record in records
            ),
            str(path),
            "partial traces do not rule out the desired regular q=1 wedge signature",
        ),
        "markdown_matches_report": gate(
            "residual records: `9`" in md_text
            and "residual blocks: `18`" in md_text
            and "high_priority_q1_or_adjacent" in md_text
            and "map-level character data" in md_text,
            str(md_path),
            "markdown exposes counts, priority bucket, and map-data interpretation",
        ),
    }
    return {
        "scope": "verification for residual enhanced radius-2 character-backlog prioritization",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_residual_backlog_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
