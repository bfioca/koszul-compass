#!/usr/bin/env python3
"""Verify the second bounded radius-2 q=1 phenomenology pilot window."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_pilot_window2.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_pilot_window2.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    pilot = report["pilot_counters"]
    topology = report["topology_counters"]
    records = report["filtered_candidate_records"]
    unresolved = [
        record
        for record in records
        if record["classification"]["category"] == "unresolved"
    ]
    no_mass = [
        record
        for record in records
        if record["classification"]["status"] == "no_certified_triplet_mass_operator_found"
    ]
    dangerous = [
        record
        for record in records
        if record["classification"]["status"]
        == "dangerous_10_5bar_5bar_operator_allowed"
    ]
    dt = [
        record
        for record in records
        if record["classification"]["status"]
        == "negative_control_doublet_triplet_obstruction"
    ]

    verification_gates = {
        "frontier_window_counts_match": gate(
            topology["unique_candidates"] == 131895
            and topology["anomaly_survivors"] == 8459
            and pilot["anomaly_frontier_size"] == 8459
            and pilot["anomaly_start"] == 1200
            and pilot["anomaly_records_screened"] == 2400
            and pilot["anomaly_records_before_window"] == 1200
            and pilot["anomaly_records_after_window"] == 4859,
            str(path),
            "window 2 records the radius-2 denominator and screened anomaly-frontier slice",
        ),
        "screening_counts_match": gate(
            pilot["slope_survivors"] == 484
            and pilot["spectrum_survivors"] == 277
            and pilot["raw_q1_spectrum_survivors"] == 12
            and pilot["raw_q1_certification_attempts"] == 12
            and pilot["character_certified_q1_survivors"] == 11
            and pilot["cohomology_exceptions"] == 1,
            str(path),
            "window 2 q=1 screening and certification counts are stable",
        ),
        "classification_counts_match": gate(
            report["summary"]["status"] == "no_viable_candidate_found_in_pilot"
            and report["summary"]["viable_count"] == 0
            and report["summary"]["categories"]
            == {"phenomenologically obstructed": 10, "unresolved": 2}
            and report["summary"]["statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 3,
                "missing_character_or_charge_level_data": 1,
                "negative_control_doublet_triplet_obstruction": 7,
                "no_certified_triplet_mass_operator_found": 1,
            },
            str(path),
            "window 2 found no viable candidate and produced the expected obstruction/unresolved split",
        ),
        "no_mass_unresolved_is_present": gate(
            len(no_mass) == 1
            and no_mass[0]["mass_operator_table"] is not None
            and all(
                not item["triplet_mass_allowed_by_current_selection_rules"]
                for item in no_mass[0]["mass_operator_table"]
            ),
            str(path),
            "one q=1 candidate remains unresolved because no certified triplet mass operator was found",
        ),
        "obstructed_records_have_operator_evidence": gate(
            len(dt) == 7
            and len(dangerous) == 3
            and all(
                any(
                    item["triplet_mass_allowed_by_current_selection_rules"]
                    and item["doublet_mass_same_selection_rule"]
                    for item in record["mass_operator_table"]
                )
                for record in dt
            )
            and all(
                any(
                    item["neutral_under_S_U1_5"]
                    and not item["forbidden_by_current_selection_rules"]
                    for item in record["proton_decay_operator_table"]
                )
                for record in dangerous
            ),
            str(path),
            "obstructed window-2 records include explicit mass or proton-decay operator evidence",
        ),
        "builder_gates_pass": gate(
            all(item["pass"] for item in report["gates"].values()),
            str(path),
            "window 2 builder gates passed",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_found_in_pilot`" in md_text
            and "anomaly_start': 1200" in md_text
            and "raw_q1_spectrum_survivors': 12" in md_text
            and "no_certified_triplet_mass_operator_found" in md_text,
            str(md_path),
            "window 2 markdown exposes scope, counts, and unresolved no-mass classification",
        ),
    }
    return {
        "scope": "verification for bounded radius-2 q=1 phenomenology pilot window 2",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_pilot_window2_verification.json"
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
