#!/usr/bin/env python3
"""Verify selected radius-4 source coverage report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_selected_source_coverage_report.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_selected_source_coverage_report.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side selected-source coverage gates passed",
        ),
        "combined_coverage_counts_match": gate(
            summary["source_records_expanded"] == 63
            and summary["frontier_records"] == 34500
            and summary["covered_records"] == 34500
            and summary["remaining_records"] == 0,
            str(path),
            "all selected radius-4 source records are covered",
        ),
        "combined_q1_counts_match": gate(
            summary["raw_q1_spectrum_survivors"] == 200
            and summary["character_certified_q1_survivors_at_scout_time"] == 96
            and summary["viable_count"] == 0,
            str(path),
            "combined q=1 survivor counts and viable count match batch reports",
        ),
        "final_checkpoint_counts_match": gate(
            summary["final_or_checkpoint_categories"]
            == {"phenomenologically obstructed": 111, "unresolved": 89}
            and summary["final_or_checkpoint_statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 31,
                "known_line_resolution_still_incomplete": 44,
                "missing_character_or_charge_level_data": 45,
                "negative_control_doublet_triplet_obstruction": 66,
                "no_triplet_mass_in_certified_singlet_monoid": 11,
                "rejected_spectrum_signature_not_q1_three_family": 3,
            },
            str(path),
            "combined final/checkpoint status totals include batch4 known-line and mass closure",
        ),
        "batch4_scope_caveat_present": gate(
            "Batch4 now has known-line resolution plus exact monoid closure" in report[
                "closure_scope_note"
            ]
            and "31 known-line-incomplete rows" in report["closure_scope_note"],
            str(path),
            "report explicitly scopes remaining batch4 character work",
        ),
        "markdown_exposes_report": gate(
            "Selected Radius-4 Source Coverage" in md_text
            and "frontier_records: `34500`" in md_text
            and "raw_q1_spectrum_survivors: `200`" in md_text,
            str(md_path),
            "markdown exposes selected-source coverage totals",
        ),
    }
    return {
        "scope": "verification for selected radius-4 source coverage report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_selected_source_coverage_report_verification.json"
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
