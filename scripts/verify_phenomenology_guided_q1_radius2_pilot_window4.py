#!/usr/bin/env python3
"""Verify the fourth bounded radius-2 q=1 phenomenology pilot window."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_pilot_window4.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_pilot_window4.md"
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
            and pilot["anomaly_start"] == 6000
            and pilot["anomaly_records_screened"] == 2459
            and pilot["anomaly_records_before_window"] == 6000
            and pilot["anomaly_records_after_window"] == 0,
            str(path),
            "window 4 records the final radius-2 anomaly-frontier slice",
        ),
        "screening_counts_match": gate(
            pilot["slope_survivors"] == 1209
            and pilot["spectrum_survivors"] == 456
            and pilot["raw_q1_spectrum_survivors"] == 10
            and pilot["raw_q1_certification_attempts"] == 10
            and pilot["character_certified_q1_survivors"] == 5
            and pilot["cohomology_exceptions"] == 1,
            str(path),
            "window 4 q=1 screening and certification counts are stable",
        ),
        "classification_counts_match": gate(
            report["summary"]["status"] == "no_viable_candidate_found_in_pilot"
            and report["summary"]["viable_count"] == 0
            and report["summary"]["categories"]
            == {"phenomenologically obstructed": 5, "unresolved": 5}
            and report["summary"]["statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 1,
                "missing_character_or_charge_level_data": 5,
                "negative_control_doublet_triplet_obstruction": 4,
            },
            str(path),
            "window 4 found no viable candidate and produced the expected obstruction/unresolved split",
        ),
        "unresolved_records_are_not_overclassified": gate(
            len(unresolved) == 5
            and all(
                record["classification"]["status"]
                == "missing_character_or_charge_level_data"
                and record["character_certificate"]["character_certified"] is False
                and record["mass_operator_table"] is None
                and record["proton_decay_operator_table"] is None
                for record in unresolved
            ),
            str(path),
            "uncertified window-4 q=1 records remain unresolved without operator tables",
        ),
        "obstructed_records_have_operator_evidence": gate(
            len(dt) == 4
            and len(dangerous) == 1
            and all(
                any(
                    item["triplet_mass_allowed_by_current_selection_rules"]
                    and item["doublet_mass_same_selection_rule"]
                    and not item.get(
                        "selective_doublet_protection_by_current_selection_rules",
                        False,
                    )
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
            "obstructed window-4 records include explicit mass or proton-decay operator evidence",
        ),
        "builder_gates_pass": gate(
            all(item["pass"] for item in report["gates"].values()),
            str(path),
            "window 4 builder gates passed",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_found_in_pilot`" in md_text
            and "anomaly_start': 6000" in md_text
            and "raw_q1_spectrum_survivors': 10" in md_text
            and "missing_character_or_charge_level_data" in md_text,
            str(md_path),
            "window 4 markdown exposes scope, counts, and unresolved classifications",
        ),
    }
    return {
        "scope": "verification for bounded radius-2 q=1 phenomenology pilot window 4",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_pilot_window4_verification.json"
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
