#!/usr/bin/env python3
"""Verify the cumulative10 twelfth Serre-orbit branch closure report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_twelfth_orbit_branch_closure.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_twelfth_orbit_branch_closure.md"
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
            "builder-side twelfth-orbit branch gates passed",
        ),
        "target_orbit_matches_cumulative10_frontier": gate(
            report["twelfth_serre_orbit"]["representative"] == [-1, 0, 2, 2, 0, -1, 0]
            and report["twelfth_serre_orbit"]["dual"] == [1, 0, -2, -2, 0, 1, 0]
            and report["twelfth_serre_orbit"]["target_candidate"]
            == "batch1:window4_radius4_adjacency_filtered_4_known_line_resolved",
            str(path),
            "branch closure targets the verified cumulative10 next Serre orbit",
        ),
        "all_trace_branches_certified": gate(
            report["summary"]["candidate_count"] == 1
            and report["summary"]["branch_count"] == len(records) == 9
            and report["summary"]["filled_blocks"] == 18
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and report["summary"]["character_certified_branches"] == 9
            and all(
                record["character_certificate"]["character_certified"]
                and has_required_sections(record)
                and record["twelfth_serre_orbit_branch_resolution"]["filled_block_count"] == 2
                and record["twelfth_serre_orbit_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                == 0
                for record in records
            ),
            str(path),
            "all single-candidate mixed-degree trace branches are fully certified",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"] == {"phenomenologically obstructed": 9}
            and report["summary"]["statuses"]
            == {
                "negative_control_doublet_triplet_obstruction": 1,
                "rejected_spectrum_signature_not_q1_three_family": 8,
            },
            str(path),
            "all twelfth-orbit branches are nonviable with exact statuses",
        ),
        "no_viable_branch_found": gate(
            report["summary"]["viable_count"] == len(viable) == 0
            and report["status"] == "no_viable_candidate_found_in_twelfth_serre_orbit_branches",
            str(path),
            "no branch of the twelfth orbit is viable",
        ),
        "markdown_exposes_closure": gate(
            "branch_count: `9`" in md_text
            and "negative_control_doublet_triplet_obstruction" in md_text
            and "rejected_spectrum_signature_not_q1_three_family" in md_text
            and "eight lose the q=1 signature" in md_text,
            str(md_path),
            "markdown exposes twelfth-orbit branch count and obstruction statuses",
        ),
    }
    return {
        "scope": "verification for cumulative10 twelfth Serre-orbit branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_twelfth_orbit_branch_closure_verification.json"
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
