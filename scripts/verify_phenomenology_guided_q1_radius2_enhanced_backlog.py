#!/usr/bin/env python3
"""Verify the enhanced radius-2 character-backlog report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog.md"
    audit_path = REPORTS / "phenomenology_guided_q1_radius2_unresolved_audit.json"
    report = load_json(path)
    audit = load_json(audit_path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["filtered_candidate_records"]
    enhanced = report["enhanced_records"]
    newly_certified = [record for record in enhanced if record["character_certified"]]
    obstructed = [
        record
        for record in records
        if record["classification"]["status"]
        == "no_triplet_mass_in_certified_singlet_monoid"
    ]
    unresolved = [
        record
        for record in records
        if record["classification"]["status"]
        == "enhanced_character_certificate_still_incomplete"
    ]

    verification_gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "enhanced backlog builder gates pass",
        ),
        "input_backlog_matches_audit": gate(
            audit["summary"]["kinds"]["missing_character_or_charge_level_data"] == 10
            and report["summary"]["input_backlog_records"] == 10
            and len(records) == len(enhanced) == 10,
            f"{audit_path}, {path}",
            "enhancement starts from the ten unresolved character-backlog records",
        ),
        "enhancement_counts_match": gate(
            report["summary"]["filled_block_count"] == 16
            and report["summary"]["remaining_unresolved_block_count"] == 18
            and report["summary"]["newly_character_certified_records"] == 1
            and len(newly_certified) == 1,
            str(path),
            "two-term enhancement fills the expected blocks and certifies one backlog record",
        ),
        "promoted_q1_record_is_obstructed": gate(
            report["summary"]["desired_q1_after_enhancement"] == 1
            and len(obstructed) == 1
            and obstructed[0]["spectrum_certificate"]["vectorlike_prediction"]
            == {
                "colored_triplet_vectorlike_pairs": 1,
                "electroweak_doublet_vectorlike_pairs": 1,
                "h1_wedge2_regular_multiplicity": 4,
                "h2_wedge2_regular_multiplicity": 1,
                "net_families": 3,
                "regular_character_rule_applies": True,
            }
            and obstructed[0]["character_certificate"]["character_certified"] is True
            and obstructed[0]["certified_singlet_monoid_mass_audit"][
                "all_mass_entries_monoid_obstructed"
            ]
            is True,
            str(path),
            "the one newly certified desired-q1 record is obstructed by certified singlet monoid support",
        ),
        "mass_monoid_obstruction_has_charge_support_evidence": gate(
            len(obstructed) == 1
            and len(obstructed[0]["certified_singlet_monoid_mass_audit"]["mass_entries"])
            == 2
            and all(
                {item["coordinate"] for item in entry["positive_support_obstructions"]}
                == {"e2", "e3"}
                for entry in obstructed[0]["certified_singlet_monoid_mass_audit"][
                    "mass_entries"
                ]
            ),
            str(path),
            "both triplet mass bilinears require positive e2/e3 support absent from certified H1 singlet generators",
        ),
        "summary_taxonomy_matches": gate(
            report["summary"]["viable_count"] == 0
            and report["summary"]["categories"]
            == {"phenomenologically obstructed": 1, "unresolved": 9}
            and report["summary"]["statuses"]
            == {
                "enhanced_character_certificate_still_incomplete": 9,
                "no_triplet_mass_in_certified_singlet_monoid": 1,
            }
            and len(unresolved) == 9,
            str(path),
            "enhanced backlog taxonomy is stable and contains no viable candidate",
        ),
        "markdown_matches_report": gate(
            "newly character-certified records: `1`" in md_text
            and "desired q=1 after enhancement: `1`" in md_text
            and "viable count: `0`" in md_text
            and "no_triplet_mass_in_certified_singlet_monoid" in md_text,
            str(md_path),
            "markdown exposes promoted q=1 count, viable count, and obstruction status",
        ),
    }
    return {
        "scope": "verification for enhanced radius-2 character-backlog report",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_enhanced_backlog_verification.json"
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
