#!/usr/bin/env python3
"""Verify the highest-demand Serre-orbit branch closure report."""

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


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["branch_records"]
    certified = [
        record for record in records if record["character_certificate"]["character_certified"]
    ]
    viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]

    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side top-orbit branch gates passed",
        ),
        "target_orbit_matches_queue": gate(
            report["top_serre_orbit"]["representative"]
            == [0, 0, -2, 1, -1, 1, -1]
            and report["top_serre_orbit"]["dual"]
            == [0, 0, 2, -1, 1, -1, 1],
            str(path),
            "branch closure targets the top missing Serre orbit",
        ),
        "branch_counts_match": gate(
            report["summary"]["candidate_count"] == 5
            and report["summary"]["branch_count"] == len(records) == 10
            and report["summary"]["filled_blocks"] == 20
            and report["summary"]["remaining_unresolved_blocks"] == 4,
            str(path),
            "both signs are tested for all top-orbit candidates and expected blocks are filled",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"]
            == {"phenomenologically obstructed": 8, "unresolved": 2}
            and report["summary"]["statuses"]
            == {
                "negative_control_doublet_triplet_obstruction": 4,
                "rejected_spectrum_signature_not_q1_three_family": 4,
                "top_serre_orbit_branch_still_character_incomplete": 2,
            },
            str(path),
            "branch classifications match the bounded top-orbit closure",
        ),
        "certified_branches_filtered": gate(
            len(certified) == report["summary"]["character_certified_branches"] == 8
            and all(
                record["classification"]["category"] == "phenomenologically obstructed"
                for record in certified
            )
            and all(has_required_sections(record) for record in records),
            str(path),
            "every character-certified top-orbit branch has deliverable sections and is filtered",
        ),
        "no_viable_branch_found": gate(
            report["summary"]["viable_count"] == len(viable) == 0
            and report["status"] == "no_viable_candidate_found_in_top_serre_orbit_branches",
            str(path),
            "neither one-dimensional Z2 character branch is viable",
        ),
        "markdown_exposes_closure": gate(
            "branch_count: `10`" in md_text
            and "negative_control_doublet_triplet_obstruction" in md_text
            and "rejected_spectrum_signature_not_q1_three_family" in md_text,
            str(md_path),
            "markdown exposes branch count and closure statuses",
        ),
    }
    return {
        "scope": "verification for highest-demand Serre-orbit branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_top_orbit_branch_closure_verification.json"
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
