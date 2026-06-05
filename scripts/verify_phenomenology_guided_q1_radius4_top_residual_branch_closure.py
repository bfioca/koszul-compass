#!/usr/bin/env python3
"""Verify the residual branch closure after the top Serre-orbit closure."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_top_residual_branch_closure.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_top_residual_branch_closure.md"
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
            "builder-side residual branch gates passed",
        ),
        "expected_orbits_present": gate(
            report["orbits"]["top"]["representative"] == [0, 0, -2, 1, -1, 1, -1]
            and report["orbits"]["residual"]["representative"]
            == [-2, 2, -1, -1, 1, 0, 1],
            str(path),
            "residual closure branches the top orbit and its remaining companion orbit",
        ),
        "six_complete_branches": gate(
            report["summary"]["branch_count"] == len(records) == 6
            and report["summary"]["filled_blocks"] == 24
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and all(
                record["character_certificate"]["character_certified"]
                and has_required_sections(record)
                for record in records
            ),
            str(path),
            "two top signs times three residual traces fully certify all branch records",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"] == {"phenomenologically obstructed": 6}
            and report["summary"]["statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 2,
                "rejected_spectrum_signature_not_q1_three_family": 4,
            },
            str(path),
            "all residual branches are nonviable with exact obstruction statuses",
        ),
        "no_viable_branch_found": gate(
            report["summary"]["viable_count"] == len(viable) == 0
            and report["status"] == "no_viable_candidate_found_in_top_residual_branches",
            str(path),
            "no completion of the residual top-orbit candidate is viable",
        ),
        "markdown_exposes_closure": gate(
            "branch_count: `6`" in md_text
            and "dangerous_10_5bar_5bar_operator_allowed" in md_text
            and "rejected_spectrum_signature_not_q1_three_family" in md_text,
            str(md_path),
            "markdown exposes residual branch count and obstruction statuses",
        ),
    }
    return {
        "scope": "verification for top residual branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_top_residual_branch_closure_verification.json"
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
