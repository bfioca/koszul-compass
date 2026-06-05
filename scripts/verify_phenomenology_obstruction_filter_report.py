#!/usr/bin/env python3
"""Verify the current-pool phenomenology obstruction filter report."""

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
    path = REPORTS / "phenomenology_obstruction_filter_report.json"
    md_path = REPORTS / "phenomenology_obstruction_filter_report.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["candidate_records"]
    q1_records = [
        record
        for record in records
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]
    ]
    negative = next(
        record
        for record in q1_records
        if record["classification"]["status"]
        == "negative_control_doublet_triplet_obstruction"
    )
    unresolved = next(
        record
        for record in q1_records
        if record["classification"]["status"] == "missing_character_or_charge_level_data"
    )
    neutral_dangerous = [
        item
        for item in negative["proton_decay_operator_table"]
        if item["operator"] == "10_1*5bar_04*5bar_23"
    ][0]
    mass_hit = [
        item
        for item in negative["mass_operator_table"]
        if item["fivebar"] == "5bar_04" and item["five"] == "5_14"
    ][0]

    verification_gates = {
        "summary_counts_match_current_pool": gate(
            report["summary"]["status"] == "no_viable_candidate_in_current_pool"
            and report["summary"]["candidate_count"] == 17
            and report["summary"]["q1_candidate_count"] == 2
            and report["summary"]["viable_count"] == 0
            and report["summary"]["categories"]
            == {"phenomenologically obstructed": 16, "unresolved": 1},
            str(path),
            "current candidate pool has no viable charge-level candidate",
        ),
        "negative_control_imported": gate(
            report["gates"]["negative_control_is_obstructed"]["pass"]
            and report["negative_control_summary"]["source"]
            == "cicy5259_lead_phenomenology_dossier.json"
            and "10_1*5bar_04*5bar_23 is neutral under S(U(1)^5)"
            in report["negative_control_summary"]["obstruction_pattern"],
            str(path),
            "5259/7914 dossier is used as the negative-control obstruction",
        ),
        "per_candidate_sections_exist": gate(
            report["gates"]["per_candidate_tables_emitted"]["pass"]
            and all(
                {
                    "spectrum_certificate",
                    "character_certificate",
                    "mass_operator_table",
                    "proton_decay_operator_table",
                    "classification",
                }.issubset(record)
                for record in records
            ),
            str(path),
            "each candidate emits the required spectrum, character, mass, proton, and classification sections",
        ),
        "q1_negative_control_rejected_for_dt_obstruction": gate(
            negative["cicy_route"] == "5259/7914"
            and negative["classification"]["category"]
            == "phenomenologically obstructed"
            and mass_hit["triplet_mass_allowed_by_current_selection_rules"]
            and mass_hit["doublet_mass_same_selection_rule"]
            and not mass_hit[
                "selection_rule_can_lift_triplet_while_protecting_doublet"
            ],
            str(path),
            "certified q=1 negative control is rejected because mass selection rules do not split triplets from doublets",
        ),
        "dangerous_operator_detected": gate(
            neutral_dangerous["neutral_under_S_U1_5"]
            and not neutral_dangerous["forbidden_by_current_selection_rules"]
            and neutral_dangerous["charge"]["coefficients"] == [1, 1, 1, 1, 1],
            str(path),
            "negative control includes the neutral dangerous 10_1*5bar_04*5bar_23 operator",
        ),
        "incomplete_q1_candidate_is_unresolved": gate(
            unresolved["classification"]["category"] == "unresolved"
            and unresolved["character_certificate"]["character_certified"] is False
            and unresolved["mass_operator_table"] is None
            and unresolved["proton_decay_operator_table"] is None,
            str(path),
            "q=1 arithmetic without complete character/charge evidence remains unresolved",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_in_current_pool`" in md_text
            and "q=1 candidate count: `2`" in md_text
            and "viable count: `0`" in md_text
            and "negative_control_doublet_triplet_obstruction" in md_text,
            str(md_path),
            "markdown exposes the filter status and negative-control rejection",
        ),
    }
    return {
        "scope": "verification for current-pool phenomenology obstruction filter report",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_obstruction_filter_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
