#!/usr/bin/env python3
"""Verify the current selected radius-4 frontier report."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_current_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_current_frontier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side current-frontier gates passed",
        ),
        "counts_match_selected_frontier": gate(
            report["summary"]["raw_q1_spectrum_survivors"] == 49
            and report["summary"]["current_obstructed_count"] == 35
            and report["summary"]["current_unresolved_count"] == 14
            and report["summary"]["viable_count"] == 0,
            str(path),
            "current selected radius-4 q=1 counts are accounted",
        ),
        "known_line_resolution_imported": gate(
            report["summary"]["character_certified_before_resolution"] == 28
            and report["summary"]["known_line_newly_character_certified"] == 7
            and report["summary"]["filled_known_line_blocks"] == 40,
            str(path),
            "current frontier includes the verified known-line resolution pass",
        ),
        "status_histogram_matches": gate(
            report["summary"]["current_statuses"]
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 7,
                "known_line_resolution_still_incomplete": 14,
                "negative_control_doublet_triplet_obstruction": 28,
            },
            str(path),
            "current status histogram matches resolved selected frontier",
        ),
        "remaining_unresolved_listed": gate(
            len(report["remaining_unresolved_records"]) == 14
            and all(record["remaining_blocks"] > 0 for record in report["remaining_unresolved_records"]),
            str(path),
            "all remaining unresolved records are listed with unresolved block counts",
        ),
        "markdown_exposes_summary": gate(
            "current_obstructed_count: `35`" in md_text
            and "current_unresolved_count: `14`" in md_text
            and "viable_count: `0`" in md_text,
            str(md_path),
            "markdown exposes current selected radius-4 frontier summary",
        ),
    }
    return {
        "scope": "verification for current selected radius-4 frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_current_frontier_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
