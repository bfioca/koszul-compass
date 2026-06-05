#!/usr/bin/env python3
"""Verify the phenomenology-guided q=1 neighborhood search report."""

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
    path = REPORTS / "phenomenology_guided_q1_search.json"
    md_path = REPORTS / "phenomenology_guided_q1_search.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["filtered_candidate_records"]
    obstructed = [
        record
        for record in records
        if record["classification"]["category"] == "phenomenologically obstructed"
    ]
    unresolved = [
        record
        for record in records
        if record["classification"]["category"] == "unresolved"
    ]
    dt_obstructed = [
        record
        for record in records
        if record["classification"]["status"]
        == "negative_control_doublet_triplet_obstruction"
    ]
    dangerous_obstructed = [
        record
        for record in records
        if record["classification"]["status"]
        == "dangerous_10_5bar_5bar_operator_allowed"
    ]

    verification_gates = {
        "search_counts_match_radius1_q1_neighborhood": gate(
            report["summary"]["status"] == "no_viable_candidate_found"
            and report["counters"]["unique_candidates"] == 559
            and report["counters"]["anomaly_survivors"] == 104
            and report["counters"]["slope_survivors"] == 50
            and report["counters"]["spectrum_survivors"] == 26
            and report["counters"]["raw_q1_spectrum_survivors"] == 4
            and report["counters"]["character_certified_q1_survivors"] == 3,
            str(path),
            "bounded radius-1 q=1 neighborhood counters are stable",
        ),
        "gates_pass": gate(
            all(item["pass"] for item in report["gates"].values()),
            str(path),
            "builder gates passed for start target, certification queue, filter application, and no viable candidate",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"]
            == {"phenomenologically obstructed": 3, "unresolved": 1}
            and report["summary"]["statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 1,
                "missing_character_or_charge_level_data": 1,
                "negative_control_doublet_triplet_obstruction": 2,
            }
            and len(obstructed) == 3
            and len(unresolved) == 1,
            str(path),
            "guided search has three obstructed q=1 candidates and one unresolved raw q=1 candidate",
        ),
        "dt_obstructions_have_mass_tables": gate(
            len(dt_obstructed) == 2
            and all(
                any(
                    item["triplet_mass_allowed_by_current_selection_rules"]
                    and item["doublet_mass_same_selection_rule"]
                    and not item[
                        "selection_rule_can_lift_triplet_while_protecting_doublet"
                    ]
                    for item in record["mass_operator_table"]
                )
                for record in dt_obstructed
            ),
            str(path),
            "doublet-triplet obstruction records contain charge-allowed mass terms with no selective doublet protection",
        ),
        "dangerous_operator_obstruction_has_proton_table": gate(
            len(dangerous_obstructed) == 1
            and any(
                not item["forbidden_by_current_selection_rules"]
                and item["neutral_under_S_U1_5"]
                for item in dangerous_obstructed[0]["proton_decay_operator_table"]
            ),
            str(path),
            "dangerous-operator obstruction records a neutral 10*5bar*5bar operator",
        ),
        "unresolved_record_lacks_character_tables": gate(
            len(unresolved) == 1
            and unresolved[0]["character_certificate"]["character_certified"] is False
            and unresolved[0]["mass_operator_table"] is None
            and unresolved[0]["proton_decay_operator_table"] is None,
            str(path),
            "uncertified raw q=1 survivor is kept unresolved rather than falsely rejected as spectrum failure",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_found`" in md_text
            and "raw q=1 count: `4`" in md_text
            and "character-certified q=1 count: `3`" in md_text
            and "viable count: `0`" in md_text
            and "missing_character_or_charge_level_data" in md_text,
            str(md_path),
            "markdown exposes guided-search counts and unresolved classification",
        ),
    }
    return {
        "scope": "verification for phenomenology-guided q=1 neighborhood search",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_search_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
