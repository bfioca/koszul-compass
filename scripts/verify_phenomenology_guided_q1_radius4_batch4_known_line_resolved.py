#!/usr/bin/env python3
"""Verify batch-4 known-line resolution report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_batch4_known_line_resolved.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_batch4_known_line_resolved.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side batch-4 known-line gates passed",
        ),
        "all_character_gaps_attempted": gate(
            summary["attempted_character_gap_records"] == 39
            and len(report["filtered_candidate_records"]) == 39,
            str(path),
            "all batch-4 scout character-gap rows were attempted",
        ),
        "resolution_accounting_match": gate(
            summary["filled_blocks"] == 68
            and summary["remaining_unresolved_blocks"] == 90
            and summary["incompatible_known_actuals"] == 44
            and summary["character_certified_records"] == 8,
            str(path),
            "known-line block accounting matches expected batch-4 totals",
        ),
        "classification_counts_match": gate(
            summary["viable_count"] == 0
            and summary["categories"] == {"phenomenologically obstructed": 7, "unresolved": 32}
            and summary["statuses"]
            == {
                "known_line_resolution_still_incomplete": 31,
                "negative_control_doublet_triplet_obstruction": 4,
                "no_certified_triplet_mass_operator_found": 1,
                "no_triplet_mass_in_certified_singlet_monoid": 1,
                "rejected_spectrum_signature_not_q1_three_family": 2,
            },
            str(path),
            "known-line classifications match expected batch-4 counts",
        ),
        "markdown_exposes_result": gate(
            "attempted_character_gap_records: `39`" in md_text
            and "known_line_resolution_still_incomplete" in md_text,
            str(md_path),
            "markdown exposes batch-4 known-line result",
        ),
    }
    return {
        "scope": "verification for batch-4 known-line resolution",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", default=str(REPORTS / "phenomenology_guided_q1_radius4_batch4_known_line_resolved_verification.json"))
    args = parser.parse_args()
    result = verify()
    Path(args.json_out).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
