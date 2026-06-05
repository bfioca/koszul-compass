#!/usr/bin/env python3
"""Verify the third bounded radius-2 q=1 phenomenology pilot window."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_pilot_window3.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_pilot_window3.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    pilot = report["pilot_counters"]
    topology = report["topology_counters"]
    records = report["filtered_candidate_records"]

    verification_gates = {
        "frontier_window_counts_match": gate(
            topology["unique_candidates"] == 131895
            and topology["anomaly_survivors"] == 8459
            and pilot["anomaly_frontier_size"] == 8459
            and pilot["anomaly_start"] == 3600
            and pilot["anomaly_records_screened"] == 2400
            and pilot["anomaly_records_before_window"] == 3600
            and pilot["anomaly_records_after_window"] == 2459,
            str(path),
            "window 3 records the radius-2 denominator and screened anomaly-frontier slice",
        ),
        "screening_counts_match": gate(
            pilot["slope_survivors"] == 373
            and pilot["spectrum_survivors"] == 134
            and pilot["raw_q1_spectrum_survivors"] == 4
            and pilot["raw_q1_certification_attempts"] == 4
            and pilot["character_certified_q1_survivors"] == 0
            and pilot["cohomology_exceptions"] == 1,
            str(path),
            "window 3 q=1 screening counts are stable and no raw q=1 survivor completed character certification",
        ),
        "classification_counts_match": gate(
            report["summary"]["status"] == "no_viable_candidate_found_in_pilot"
            and report["summary"]["viable_count"] == 0
            and report["summary"]["categories"] == {"unresolved": 4}
            and report["summary"]["statuses"]
            == {"missing_character_or_charge_level_data": 4},
            str(path),
            "window 3 q=1 survivors are all unresolved due missing character/charge-level data",
        ),
        "records_are_unresolved_without_operator_tables": gate(
            len(records) == 4
            and all(
                record["classification"]["category"] == "unresolved"
                and record["character_certificate"]["character_certified"] is False
                and record["mass_operator_table"] is None
                and record["proton_decay_operator_table"] is None
                for record in records
            ),
            str(path),
            "window 3 records do not overclassify uncertified q=1 candidates",
        ),
        "builder_gates_pass": gate(
            all(item["pass"] for item in report["gates"].values()),
            str(path),
            "window 3 builder gates passed",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_found_in_pilot`" in md_text
            and "anomaly_start': 3600" in md_text
            and "raw_q1_spectrum_survivors': 4" in md_text
            and "missing_character_or_charge_level_data" in md_text,
            str(md_path),
            "window 3 markdown exposes scope, counts, and unresolved classifications",
        ),
    }
    return {
        "scope": "verification for bounded radius-2 q=1 phenomenology pilot window 3",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_pilot_window3_verification.json"
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
