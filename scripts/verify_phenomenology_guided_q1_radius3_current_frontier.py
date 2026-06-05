#!/usr/bin/env python3
"""Verify the current radius-3 q=1 frontier summary."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_current_frontier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    high_priority = report["high_priority_unresolved_frontier"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side current-frontier gates passed",
        ),
        "counts_accounted": gate(
            summary["raw_q1_spectrum_survivors"] == 64
            and summary["current_obstructed_count"] == 63
            and summary["current_unresolved_count"] == 1
            and summary["current_obstructed_count"]
            + summary["current_unresolved_count"]
            == summary["raw_q1_spectrum_survivors"]
            and summary["viable_count"] == 0,
            str(path),
            "all raw q=1 survivors are obstructed or unresolved after audit",
        ),
        "high_priority_records_emitted": gate(
            len(high_priority) == 1
            and all(
                record["missing_character_block_count"] <= 2
                for record in high_priority
            ),
            str(path),
            "one remaining high-priority sign-conflict unresolved record is emitted",
        ),
        "markdown_exposes_frontier": gate(
            "Status: `no_viable_candidate_found_radius3_frontier_partly_unresolved`"
            in md_text
            and "current_obstructed_count: `63`" in md_text
            and "current_unresolved_count: `1`" in md_text,
            str(md_path),
            "markdown exposes current frontier status and counts",
        ),
    }
    return {
        "scope": "verification for current radius-3 q=1 frontier summary",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_current_frontier_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
