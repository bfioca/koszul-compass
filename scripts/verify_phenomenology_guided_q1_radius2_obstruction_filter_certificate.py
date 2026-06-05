#!/usr/bin/env python3
"""Verify the final radius-2 obstruction-filter certificate."""

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


def has_required_sections(record: dict[str, Any]) -> bool:
    return {
        "spectrum_certificate",
        "character_certificate",
        "mass_operator_table",
        "proton_decay_operator_table",
        "classification",
    }.issubset(record)


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius2_obstruction_filter_certificate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_obstruction_filter_certificate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["candidate_records"]
    raw_keys = [record["raw_candidate_key"] for record in records]
    desired = [
        record
        for record in records
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]
    ]
    statuses = report["summary"]["statuses"]
    negative_control_records = [
        record
        for record in records
        if record["classification"]["status"]
        == "negative_control_doublet_triplet_obstruction"
    ]
    dangerous_records = [
        record
        for record in records
        if record["classification"]["status"]
        == "dangerous_10_5bar_5bar_operator_allowed"
    ]

    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side closure gates all passed",
        ),
        "candidate_count_and_keys": gate(
            len(records) == len(set(raw_keys)) == 29
            and report["summary"]["raw_q1_attempts"] == 29,
            str(path),
            "certificate has exactly one unique final record per raw q=1 attempt",
        ),
        "all_final_records_are_obstructed": gate(
            report["summary"]["categories"] == {"phenomenologically obstructed": 29}
            and report["summary"]["unresolved"] == 0
            and report["summary"]["viable"] == 0,
            str(path),
            "all final radius-2 records are classified as phenomenologically obstructed",
        ),
        "required_sections_and_tables_present": gate(
            all(has_required_sections(record) for record in records)
            and all(record["mass_operator_table"] is not None for record in records)
            and all(record["proton_decay_operator_table"] is not None for record in records),
            str(path),
            "every candidate emits spectrum, character, mass, proton, and classification tables",
        ),
        "desired_q1_records_closed": gate(
            len(desired) == 28
            and all(
                record["classification"]["category"] == "phenomenologically obstructed"
                for record in desired
            ),
            str(path),
            "every final desired-q1 spectrum record is obstructed",
        ),
        "obstruction_filter_statuses_present": gate(
            statuses
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 5,
                "negative_control_doublet_triplet_obstruction": 20,
                "no_triplet_mass_in_certified_singlet_monoid": 3,
                "rejected_spectrum_signature_not_q1_three_family": 1,
            }
            and len(negative_control_records) == 20
            and len(dangerous_records) == 5,
            str(path),
            "final status distribution matches the closed radius-2 obstruction ledger",
        ),
        "markdown_exposes_summary": gate(
            "Status: `radius2_filter_closed_no_viable_candidate`" in md_text
            and "raw q=1 attempts: `29`" in md_text
            and "viable: `0`" in md_text
            and "negative_control_doublet_triplet_obstruction" in md_text,
            str(md_path),
            "markdown report exposes the closed filter summary",
        ),
    }
    return {
        "scope": "verification for final radius-2 obstruction-filter certificate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_obstruction_filter_certificate_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
