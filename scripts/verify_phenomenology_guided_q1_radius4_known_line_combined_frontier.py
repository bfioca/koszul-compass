#!/usr/bin/env python3
"""Verify the combined selected radius-4 known-line frontier ledger."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_known_line_combined_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_known_line_combined_frontier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]

    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "combined builder gates passed",
        ),
        "expected_batches_present": gate(
            summary["batches"] == ["batch1", "batch2"]
            and [item["batch"] for item in report["per_batch"]] == ["batch1", "batch2"],
            str(path),
            "combined frontier includes the first two selected radius-4 batches",
        ),
        "combined_counts_match": gate(
            summary["attempted_unresolved_records"] == 45
            and summary["filled_blocks"] == 92
            and summary["remaining_unresolved_blocks"] == 70
            and summary["incompatible_known_actuals"] == 26
            and summary["character_certified_records"] == 18,
            str(path),
            "combined known-line counts match exact batch-1 plus batch-2 totals",
        ),
        "classification_counts_match": gate(
            summary["categories"] == {"phenomenologically obstructed": 17, "unresolved": 28}
            and summary["statuses"]
            == {
                "known_line_resolution_still_incomplete": 27,
                "negative_control_doublet_triplet_obstruction": 16,
                "no_certified_triplet_mass_operator_found": 1,
                "no_triplet_mass_in_certified_singlet_monoid": 1,
            },
            str(path),
            "classification counts match the selected known-line frontier",
        ),
        "no_viable_candidate_found": gate(
            report["status"] == "no_viable_candidate_found_in_combined_known_line_frontier"
            and summary["viable_count"] == 0,
            str(path),
            "no combined known-line-resolved selected radius-4 record is viable",
        ),
        "markdown_exposes_frontier": gate(
            "Status: `no_viable_candidate_found_in_combined_known_line_frontier`"
            in md_text
            and "attempted_unresolved_records: `45`" in md_text
            and "negative_control_doublet_triplet_obstruction" in md_text,
            str(md_path),
            "markdown exposes the combined frontier status and obstruction pattern",
        ),
    }
    return {
        "scope": "verification for combined selected radius-4 known-line frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_known_line_combined_frontier_verification.json"
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
