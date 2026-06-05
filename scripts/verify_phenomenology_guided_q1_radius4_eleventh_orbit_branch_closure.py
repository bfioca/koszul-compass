#!/usr/bin/env python3
"""Verify the cumulative9 eleventh Serre-orbit partial branch closure report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_eleventh_orbit_branch_closure.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_eleventh_orbit_branch_closure.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["branch_records"]
    unresolved = [
        record for record in records if record["classification"]["category"] == "unresolved"
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side eleventh-orbit partial closure gates passed",
        ),
        "target_orbit_matches_cumulative9_frontier": gate(
            report["eleventh_serre_orbit"]["representative"] == [-2, 0, 1, -1, 0, 0, 2]
            and report["eleventh_serre_orbit"]["dual"] == [2, 0, -1, 1, 0, 0, -2]
            and report["eleventh_serre_orbit"]["target_candidate"]
            == "batch1:window4_radius4_adjacency_filtered_0_known_line_resolved",
            str(path),
            "branch closure targets the verified cumulative9 next Serre orbit",
        ),
        "partial_trace_branches_recorded": gate(
            report["summary"]["candidate_count"] == 1
            and report["summary"]["branch_count"] == len(records) == 3
            and report["summary"]["filled_blocks"] == 6
            and report["summary"]["remaining_unresolved_blocks"] == 30
            and report["summary"]["character_certified_branches"] == 0
            and all(
                not record["character_certificate"]["character_certified"]
                and has_required_sections(record)
                and record["eleventh_serre_orbit_branch_resolution"]["filled_block_count"] == 2
                and record["eleventh_serre_orbit_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                == 10
                for record in records
            ),
            str(path),
            "all three dimension-two trace branches are recorded but remain character-incomplete",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"] == {"unresolved": 3}
            and report["summary"]["statuses"]
            == {"eleventh_serre_orbit_branch_still_character_incomplete": 3}
            and len(unresolved) == 3,
            str(path),
            "eleventh-orbit branches expose five residual missing Serre orbits exactly",
        ),
        "no_viable_branch_claim_is_partial": gate(
            report["summary"]["viable_count"] == 0
            and report["status"] == "no_viable_candidate_found_in_eleventh_serre_orbit_branches"
            and report["summary"]["character_certified_branches"] == 0,
            str(path),
            "the no-viable status is explicitly before five residual-orbit closures",
        ),
        "markdown_exposes_partial_closure": gate(
            "branch_count: `3`" in md_text
            and "remaining_unresolved_blocks: `30`" in md_text
            and "leave five additional dimension-two Serre orbits unresolved" in md_text,
            str(md_path),
            "markdown exposes residual incompleteness instead of claiming full closure",
        ),
    }
    return {
        "scope": "verification for cumulative9 eleventh Serre-orbit partial branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_eleventh_orbit_branch_closure_verification.json"
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
