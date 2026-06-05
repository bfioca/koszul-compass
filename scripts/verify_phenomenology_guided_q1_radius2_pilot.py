#!/usr/bin/env python3
"""Verify the bounded radius-2 phenomenology-guided q=1 pilot report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_pilot.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_pilot.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    pilot = report["pilot_counters"]
    topology = report["topology_counters"]
    records = report["filtered_candidate_records"]
    dt = [
        record
        for record in records
        if record["classification"]["status"]
        == "negative_control_doublet_triplet_obstruction"
    ]
    dangerous = [
        record
        for record in records
        if record["classification"]["status"]
        == "dangerous_10_5bar_5bar_operator_allowed"
    ]

    verification_gates = {
        "frontier_denominator_and_caps_match": gate(
            topology["unique_candidates"] == 131895
            and topology["anomaly_survivors"] == 8459
            and pilot["anomaly_frontier_size"] == 8459
            and pilot["anomaly_records_screened"] == 1200
            and pilot["anomaly_records_unscreened"] == 7259,
            str(path),
            "pilot records the full radius-2 anomaly frontier denominator and the screened subset",
        ),
        "pilot_screening_counts_match": gate(
            pilot["slope_survivors"] == 61
            and pilot["spectrum_survivors"] == 35
            and pilot["raw_q1_spectrum_survivors"] == 3
            and pilot["raw_q1_certification_attempts"] == 3
            and pilot["character_certified_q1_survivors"] == 3,
            str(path),
            "screened subset produced three fully certified raw q=1 survivors",
        ),
        "classification_counts_match": gate(
            report["summary"]["status"] == "no_viable_candidate_found_in_pilot"
            and report["summary"]["viable_count"] == 0
            and report["summary"]["categories"]
            == {"phenomenologically obstructed": 3}
            and report["summary"]["statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 1,
                "negative_control_doublet_triplet_obstruction": 2,
            },
            str(path),
            "pilot found no viable candidate; all certified q=1 survivors are obstructed",
        ),
        "dt_obstructions_have_mass_hits": gate(
            len(dt) == 2
            and all(
                any(
                    item["triplet_mass_allowed_by_current_selection_rules"]
                    and item["doublet_mass_same_selection_rule"]
                    and not item[
                        "selection_rule_can_lift_triplet_while_protecting_doublet"
                    ]
                    for item in record["mass_operator_table"]
                )
                for record in dt
            ),
            str(path),
            "doublet-triplet obstructed pilot records have charge-allowed mass hits with no selective doublet protection",
        ),
        "dangerous_operator_record_has_neutral_operator": gate(
            len(dangerous) == 1
            and any(
                item["neutral_under_S_U1_5"]
                and not item["forbidden_by_current_selection_rules"]
                for item in dangerous[0]["proton_decay_operator_table"]
            ),
            str(path),
            "dangerous-operator pilot record has a neutral 10*5bar*5bar operator",
        ),
        "builder_gates_pass": gate(
            all(item["pass"] for item in report["gates"].values()),
            str(path),
            "pilot builder gates passed",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_found_in_pilot`" in md_text
            and "not an exhaustive radius-2 no-go" in md_text
            and "anomaly_records_screened': 1200" in md_text
            and "viable_count" not in md_text.lower(),
            str(md_path),
            "markdown exposes bounded pilot status and scope caveat",
        ),
    }
    return {
        "scope": "verification for bounded radius-2 q=1 phenomenology pilot",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_pilot_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
