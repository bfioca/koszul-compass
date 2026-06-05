#!/usr/bin/env python3
"""Verify current radius-2 q=1 frontier report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_current_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_current_frontier.md"
    rank_path = REPORTS / "phenomenology_guided_q1_radius2_rank_resolved_backlog.json"
    report = load_json(path)
    rank = load_json(rank_path)
    md_text = md_path.read_text(encoding="utf-8")
    medium = report["remaining_medium_frontier"]

    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "current-frontier builder gates pass",
        ),
        "counts_match_current_frontier": gate(
            report["summary"] == {
                "raw_q1_spectrum_survivors": 29,
                "current_obstructed_count": 29,
                "current_unresolved_count": 0,
                "viable_count": 0,
                "high_priority_rank_resolved_desired_q1": 4,
                "high_priority_rank_resolved_obstructed": 4,
                "remaining_medium_records": 5,
                "remaining_medium_currently_desired_q1": 0,
                "remaining_medium_two_term_supported_records": 3,
                "remaining_medium_unsupported_three_term_records": 2,
                "remaining_medium_desired_q1_rank_scenarios": 6,
                "medium_rank_resolved_desired_q1": 4,
                "medium_rank_resolved_obstructed": 5,
                "medium_rank_resolved_remaining_unresolved": 0,
            },
            str(path),
            "frontier accounting is 29 obstructed plus 0 unresolved records",
        ),
        "high_priority_closure_imported": gate(
            rank["summary"]["desired_q1_records"] == 4
            and rank["summary"]["categories"] == {"phenomenologically obstructed": 4}
            and rank["summary"]["remaining_unresolved_blocks"] == 0,
            f"{path}, {rank_path}",
            "rank-resolved high-priority closure is imported",
        ),
        "remaining_medium_records_are_not_current_q1": gate(
            len(medium) == 5
            and all(
                not (
                    item["current_prediction_after_enhancement"].get(
                        "regular_character_rule_applies"
                    )
                    and item["current_prediction_after_enhancement"].get("net_families")
                    == 3
                    and item["current_prediction_after_enhancement"].get(
                        "colored_triplet_vectorlike_pairs"
                    )
                    == 1
                    and item["current_prediction_after_enhancement"].get(
                        "electroweak_doublet_vectorlike_pairs"
                    )
                    == 1
                )
                for item in medium
            ),
            str(path),
            "remaining medium records are trace-feasible but not currently desired-q1",
        ),
        "markdown_matches_report": gate(
            "Status: `no_viable_candidate_found_high_priority_frontier_closed`" in md_text
            and "current_obstructed_count: `29`" in md_text
            and "current_unresolved_count: `0`" in md_text
            and "remaining_medium_currently_desired_q1: `0`" in md_text,
            str(md_path),
            "markdown exposes current frontier counts",
        ),
    }
    return {
        "scope": "verification for current radius-2 q=1 frontier report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_current_frontier_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    Path(args.json_out).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
