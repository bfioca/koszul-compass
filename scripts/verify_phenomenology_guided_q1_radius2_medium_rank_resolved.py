#!/usr/bin/env python3
"""Verify medium-priority rank-resolved backlog report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_medium_rank_resolved.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_medium_rank_resolved.md"
    scenarios_path = REPORTS / "phenomenology_guided_q1_radius2_medium_map_scenarios.json"
    report = load_json(path)
    scenarios = load_json(scenarios_path)
    md_text = md_path.read_text(encoding="utf-8")
    filtered = report["filtered_candidate_records"]
    desired_q1 = [
        record
        for record in filtered
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "medium rank-resolved builder gates pass",
        ),
        "imports_medium_scenarios": gate(
            scenarios["summary"]["two_term_supported_records"] == 3
            and scenarios["summary"]["unsupported_three_term_records"] == 2,
            f"{path}, {scenarios_path}",
            "medium rank resolution imports the verified medium scenario split",
        ),
        "summary_counts_match": gate(
            report["summary"] == {
                "medium_records": 5,
                "filled_blocks": 10,
                "remaining_unresolved_blocks": 0,
                "character_certified_records": 5,
                "desired_q1_records": 4,
                "viable_count": 0,
                "categories": {"phenomenologically obstructed": 5},
                "statuses": {
                    "negative_control_doublet_triplet_obstruction": 3,
                    "no_triplet_mass_in_certified_singlet_monoid": 1,
                    "rejected_spectrum_signature_not_q1_three_family": 1,
                },
            },
            str(path),
            "medium rank resolution certifies all five medium records",
        ),
        "desired_q1_records_are_obstructed": gate(
            len(desired_q1) == 4
            and all(
                record["classification"]["category"] == "phenomenologically obstructed"
                for record in desired_q1
            ),
            str(path),
            "new medium desired-q1 records are all phenomenologically obstructed",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_found_after_medium_rank_resolution`" in md_text
            and "desired_q1_records: `4`" in md_text
            and "remaining_unresolved_blocks: `0`" in md_text,
            str(md_path),
            "markdown exposes medium rank-resolution counts",
        ),
    }
    return {
        "scope": "verification for medium-priority rank-resolved backlog report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_medium_rank_resolved_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    Path(args.json_out).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
