#!/usr/bin/env python3
"""Verify the cumulative7 ninth/residual Serre-orbit branch closure report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_ninth_residual_branch_closure.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_ninth_residual_branch_closure.md"
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
            "builder-side ninth/residual branch gates passed",
        ),
        "target_orbits_match_frontier": gate(
            report["orbits"]["ninth"]["representative"] == [-2, 0, -3, 0, 1, 1, 0]
            and report["orbits"]["ninth"]["dual"] == [2, 0, 3, 0, -1, -1, 0]
            and report["orbits"]["residual"]["representative"]
            == [-1, 0, -3, 0, 0, 1, 0]
            and report["orbits"]["residual"]["dual"] == [1, 0, 3, 0, 0, -1, 0]
            and report["target_candidate"]
            == "batch2:window3_radius4_adjacency_filtered_1_known_line_resolved",
            str(path),
            "combined branch closure targets the cumulative7 ninth orbit and its residual orbit",
        ),
        "all_combined_branches_certified": gate(
            report["summary"]["candidate_count"] == 1
            and report["summary"]["branch_count"] == len(records) == 45
            and report["summary"]["filled_blocks"] == 180
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and report["summary"]["character_certified_branches"] == 45
            and all(
                record["character_certificate"]["character_certified"]
                and has_required_sections(record)
                and record["ninth_residual_branch_resolution"]["filled_block_count"] == 4
                and record["ninth_residual_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                == 0
                for record in records
            ),
            str(path),
            "five ninth traces times nine residual traces fully certify the target candidate",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"] == {"phenomenologically obstructed": 45}
            and report["summary"]["statuses"]
            == {
                "negative_control_doublet_triplet_obstruction": 3,
                "rejected_spectrum_signature_not_q1_three_family": 42,
            },
            str(path),
            "all combined branches are nonviable with exact obstruction counts",
        ),
        "no_viable_branch_found": gate(
            report["summary"]["viable_count"] == len(viable) == 0
            and report["status"] == "no_viable_candidate_found_in_ninth_residual_branches",
            str(path),
            "no ninth/residual completion produces a viable candidate",
        ),
        "markdown_exposes_closure": gate(
            "branch_count: `45`" in md_text
            and "remaining_unresolved_blocks: `0`" in md_text
            and "negative_control_doublet_triplet_obstruction" in md_text
            and "rejected_spectrum_signature_not_q1_three_family" in md_text
            and "42 branches lose the q=1 signature" in md_text,
            str(md_path),
            "markdown exposes the full closure and exact obstruction split",
        ),
    }
    return {
        "scope": "verification for cumulative7 ninth/residual Serre-orbit branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_ninth_residual_branch_closure_verification.json"
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
