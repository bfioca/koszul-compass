#!/usr/bin/env python3
"""Verify the radius-2 unresolved q=1 frontier audit."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.md"
    aggregate_path = REPORTS / "phenomenology_guided_q1_radius2_aggregate.json"
    report = load_json(path)
    aggregate = load_json(aggregate_path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["records"]
    backlog = [
        record
        for record in records
        if record["audit"]["kind"] == "missing_character_or_charge_level_data"
    ]
    no_mass = [
        record
        for record in records
        if record["audit"]["kind"] == "certified_record_without_triplet_mass"
    ]
    missing_blocks = [
        block
        for record in backlog
        for block in record["audit"]["missing_character_blocks"]
    ]
    no_mass_entries = no_mass[0]["audit"]["mass_entries"] if no_mass else []

    verification_gates = {
        "audit_builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "unresolved audit builder gates pass",
        ),
        "unresolved_counts_match_aggregate": gate(
            aggregate["aggregate_categories"]["unresolved"] == 11
            and report["summary"]["unresolved_records"] == 11
            and len(records) == 11,
            f"{aggregate_path}, {path}",
            "audit includes all unresolved q=1 records from the verified aggregate",
        ),
        "backlog_records_have_explicit_missing_blocks": gate(
            len(backlog) == 10
            and report["summary"]["missing_character_block_count"] == 34
            and len(missing_blocks) == 34
            and all(
                block["sector"] in {"wedge2_V", "wedge2_V_dual"}
                and block["missing_degree_keys"]
                and block["method"] == "not_determined"
                for block in missing_blocks
            ),
            str(path),
            "ten records remain unresolved because explicit wedge-sector character blocks are missing",
        ),
        "certified_no_mass_record_is_monoid_obstructed": gate(
            len(no_mass) == 1
            and no_mass[0]["character_certified"] is True
            and no_mass[0]["audit"]["recommended_classification"]
            == "phenomenologically obstructed"
            and no_mass[0]["audit"]["recommended_status"]
            == "no_triplet_mass_in_certified_singlet_monoid"
            and len(no_mass_entries) == 1
            and no_mass_entries[0]["needed_singlet_charge"]["label"]
            == "-e0+e1+e3-e4"
            and no_mass_entries[0]["certified_singlet_monoid_obstructed"] is True
            and no_mass_entries[0]["positive_support_obstructions"][0]["coordinate"]
            == "e3",
            str(path),
            "the character-certified no-mass record cannot lift the triplet using its certified H1 singlet monoid",
        ),
        "summary_taxonomy_matches": gate(
            report["summary"]["kinds"]
            == {
                "certified_record_without_triplet_mass": 1,
                "missing_character_or_charge_level_data": 10,
            }
            and report["summary"]["recommended_categories"]
            == {"phenomenologically obstructed": 1, "unresolved": 10}
            and report["summary"]["recommended_statuses"]
            == {
                "character_certificate_backlog": 10,
                "no_triplet_mass_in_certified_singlet_monoid": 1,
            },
            str(path),
            "audit taxonomy is stable",
        ),
        "markdown_matches_report": gate(
            "unresolved records: `11`" in md_text
            and "missing character blocks: `34`" in md_text
            and "no_triplet_mass_in_certified_singlet_monoid" in md_text
            and "-e0+e1+e3-e4" in md_text,
            str(md_path),
            "markdown exposes unresolved count, missing-block count, and monoid obstruction",
        ),
    }
    return {
        "scope": "verification for radius-2 unresolved q=1 frontier audit",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit_verification.json"
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
