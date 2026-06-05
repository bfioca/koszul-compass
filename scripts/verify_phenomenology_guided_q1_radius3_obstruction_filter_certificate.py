#!/usr/bin/env python3
"""Verify the radius-3 obstruction-filter certificate."""

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


def has_required_tables(record: dict[str, Any]) -> bool:
    return (
        has_required_sections(record)
        and record["mass_operator_table"] is not None
        and record["proton_decay_operator_table"] is not None
    )


def raw_key(record: dict[str, Any]) -> str:
    return f"{record.get('source_window')}/{record.get('source_filtered_label')}"


def desired_q1(record: dict[str, Any]) -> bool:
    return bool(
        record["spectrum_certificate"]["desired_q1_three_family_signature"]
    )


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius3_obstruction_filter_certificate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_obstruction_filter_certificate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["strict_candidate_records"]
    branches = report["sign_conflict_branch_records"]
    all_records = records + branches
    strict_unresolved = [
        record for record in records if record["classification"]["category"] == "unresolved"
    ]
    strict_viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]
    branch_viable = [
        record for record in branches if record["classification"]["category"] == "viable"
    ]
    desired = [record for record in records if desired_q1(record)]
    desired_unresolved = [
        record for record in desired if record["classification"]["category"] == "unresolved"
    ]
    table_certified_strict = [record for record in records if has_required_tables(record)]
    negative_control_records = [
        record
        for record in all_records
        if record["classification"]["status"]
        == "negative_control_doublet_triplet_obstruction"
    ]
    dangerous_records = [
        record
        for record in all_records
        if record["classification"]["status"]
        == "dangerous_10_5bar_5bar_operator_allowed"
    ]

    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side obstruction-filter gates passed",
        ),
        "candidate_count_and_unique_keys": gate(
            len(records) == len({raw_key(record) for record in records}) == 64
            and report["summary"]["strict_raw_q1_survivors"] == 64,
            str(path),
            "strict ledger has exactly one record per raw radius-3 q=1 survivor",
        ),
        "strict_counts_match_expected_frontier": gate(
            report["summary"]["strict_categories"]
            == {"phenomenologically obstructed": 63, "unresolved": 1}
            and report["summary"]["strict_viable"] == 0
            and report["summary"]["strict_desired_q1_records"] == 46,
            str(path),
            "strict radius-3 frontier counts match the bounded obstruction ledger",
        ),
        "tables_present_for_all_character_certified_strict_records": gate(
            len(table_certified_strict) == 63
            and all(has_required_sections(record) for record in records),
            str(path),
            "all classified strict records emit spectrum, character, mass, proton, and classification tables",
        ),
        "strict_unresolved_is_only_sign_conflict": gate(
            len(strict_unresolved) == 1
            and len(desired_unresolved) == 0
            and raw_key(strict_unresolved[0]) == "window2/radius3_adjacency_filtered_16"
            and strict_unresolved[0]["mass_operator_table"] is None
            and strict_unresolved[0]["proton_decay_operator_table"] is None,
            str(path),
            "the only strict table gap is the known sign-conflict character certificate",
        ),
        "sign_conflict_branches_are_table_certified_nonviable": gate(
            len(branches) == 2
            and all(has_required_tables(record) for record in branches)
            and all(
                raw_key(record) == "window2/radius3_adjacency_filtered_16"
                for record in branches
            )
            and len(branch_viable) == 0
            and report["summary"]["branch_categories"]
            == {"phenomenologically obstructed": 2},
            str(path),
            "both dimension-compatible sign-conflict branches have required tables and are nonviable",
        ),
        "negative_control_filter_is_active": gate(
            len(negative_control_records) == 33
            and report["negative_control"]["classification"]["category"]
            == "phenomenologically obstructed"
            and report["negative_control"]["obstruction_status"]
            == "phenomenologically_obstructed_by_current_charge_level_evidence",
            str(path),
            "5259/7914 doublet-triplet obstruction is represented as an active rejection status",
        ),
        "dangerous_operator_filter_is_active": gate(
            len(dangerous_records) == 10
            and report["summary"]["dangerous_operator_obstructions"] == 10,
            str(path),
            "dangerous 10*5bar*5bar operators remain an active rejection status",
        ),
        "no_viable_candidate_found": gate(
            len(strict_viable) == 0
            and len(branch_viable) == 0
            and report["summary"]["effective_viable"] == 0,
            str(path),
            "no strict record or branch completion passes the charge-level filter",
        ),
        "markdown_exposes_filter_summary": gate(
            "Status: `radius3_filter_closed_no_viable_candidate_one_strict_sign_conflict`"
            in md_text
            and "strict_raw_q1_survivors: `64`" in md_text
            and "effective_viable: `0`" in md_text
            and "Sign-Conflict Branch Ledger" in md_text,
            str(md_path),
            "markdown exposes the filter summary and sign-conflict branch ledger",
        ),
    }
    return {
        "scope": "verification for radius-3 obstruction-filter certificate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius3_obstruction_filter_certificate_verification.json"
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
