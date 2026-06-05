#!/usr/bin/env python3
"""Verify the bounded radius-4 unresolved branch analysis."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["record_branch_reports"]
    evaluated = [record for record in records if not record["skipped"]]
    skipped = [record for record in records if record["skipped"]]
    branches = report["branch_candidate_records"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side branch-analysis gates passed",
        ),
        "all_remaining_unresolved_accounted": gate(
            report["summary"]["unresolved_records"] == len(records) == 14
            and len(evaluated) == report["summary"]["records_evaluated"] == 13
            and len(skipped) == report["summary"]["records_skipped"] == 1,
            str(path),
            "all remaining selected radius-4 unresolved records are evaluated or explicitly skipped",
        ),
        "branch_counts_match": gate(
            report["summary"]["branches_evaluated"] == len(branches) == 646
            and report["summary"]["desired_q1_branches"] == 102
            and report["summary"]["viable_branches"] == 0,
            str(path),
            "branch totals match emitted branch candidate certificates",
        ),
        "classification_histogram_matches": gate(
            report["summary"]["categories"] == {"phenomenologically obstructed": 646}
            and report["summary"]["statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 27,
                "negative_control_doublet_triplet_obstruction": 75,
                "rejected_spectrum_signature_not_q1_three_family": 544,
            },
            str(path),
            "all evaluated branches are classified with the expected obstruction statuses",
        ),
        "skipped_record_is_large_branch_space": gate(
            len(skipped) == 1
            and skipped[0]["label"] == "window4/radius4_adjacency_filtered_0"
            and skipped[0]["branch_space_size"] == 531441,
            str(path),
            "only the large 12-block branch space is skipped",
        ),
        "branch_records_have_required_sections": gate(
            all(
                {
                    "spectrum_certificate",
                    "character_certificate",
                    "mass_operator_table",
                    "proton_decay_operator_table",
                    "classification",
                }.issubset(record)
                for record in branches
            )
            and all(record["mass_operator_table"] is not None for record in branches)
            and all(record["proton_decay_operator_table"] is not None for record in branches),
            str(path),
            "every evaluated branch emits required certificate sections and mass/proton tables",
        ),
        "markdown_exposes_summary": gate(
            "branches_evaluated: `646`" in md_text
            and "desired_q1_branches: `102`" in md_text
            and "viable_branches: `0`" in md_text
            and "skipped; branch space `531441`" in md_text,
            str(md_path),
            "markdown exposes branch-analysis summary and skipped record",
        ),
    }
    return {
        "scope": "verification for bounded radius-4 unresolved branch analysis",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_unresolved_branch_analysis_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
