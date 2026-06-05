#!/usr/bin/env python3
"""Verify the cumulative5 seventh Serre-orbit branch closure report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_seventh_orbit_branch_closure.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_seventh_orbit_branch_closure.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["branch_records"]
    viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side seventh-orbit branch gates passed",
        ),
        "target_orbit_matches_cumulative5_frontier": gate(
            report["seventh_serre_orbit"]["representative"] == [0, 0, -1, -3, 0, 1, 1]
            and report["seventh_serre_orbit"]["dual"] == [0, 0, 1, 3, 0, -1, -1]
            and report["seventh_serre_orbit"]["target_candidates"]
            == [
                "batch1:window5_radius4_adjacency_filtered_2_known_line_resolved",
                "batch1:window5_radius4_adjacency_filtered_6_known_line_resolved",
            ],
            str(path),
            "branch closure targets the verified cumulative5 next Serre orbit",
        ),
        "all_trace_branches_certified": gate(
            report["summary"]["candidate_count"] == 2
            and report["summary"]["branch_count"] == len(records) == 14
            and report["summary"]["filled_blocks"] == 28
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and report["summary"]["character_certified_branches"] == 14
            and all(
                record["character_certificate"]["character_certified"]
                and has_required_sections(record)
                for record in records
            ),
            str(path),
            "all two-candidate dimension-six trace branches are fully certified",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"] == {"phenomenologically obstructed": 14}
            and report["summary"]["statuses"]
            == {
                "negative_control_doublet_triplet_obstruction": 2,
                "rejected_spectrum_signature_not_q1_three_family": 12,
            },
            str(path),
            "all seventh-orbit branches are nonviable with exact statuses",
        ),
        "no_viable_branch_found": gate(
            report["summary"]["viable_count"] == len(viable) == 0
            and report["status"] == "no_viable_candidate_found_in_seventh_serre_orbit_branches",
            str(path),
            "no trace branch of the seventh orbit is viable",
        ),
        "markdown_exposes_closure": gate(
            "branch_count: `14`" in md_text
            and "negative_control_doublet_triplet_obstruction" in md_text
            and "rejected_spectrum_signature_not_q1_three_family" in md_text,
            str(md_path),
            "markdown exposes seventh-orbit branch count and obstruction statuses",
        ),
    }
    return {
        "scope": "verification for cumulative5 seventh Serre-orbit branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_seventh_orbit_branch_closure_verification.json"
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
