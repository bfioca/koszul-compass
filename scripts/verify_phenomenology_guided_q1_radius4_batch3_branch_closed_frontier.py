#!/usr/bin/env python3
"""Verify batch-3 branch-closed frontier summary."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_closed_frontier.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_closed_frontier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side batch3 branch-closed frontier gates passed",
        ),
        "batch3_branch_closure_counts_match": gate(
            summary["known_line_incomplete_records_closed"] == 13
            and summary["branch_records_evaluated"] == 13
            and summary["branch_records_skipped"] == 0
            and summary["branches_evaluated"] == 647
            and summary["desired_q1_branches"] == 97
            and summary["viable_branches"] == 0,
            str(path),
            "batch3 branch-closed frontier counts match source reports",
        ),
        "mass_bound_uncertainties_closed": gate(
            summary["mass_bound_branches_upgraded"] == 2
            and summary["open_mass_bound_uncertainties"] == 0
            and "no_certified_triplet_mass_operator_found"
            not in summary["adjusted_branch_statuses"],
            str(path),
            "exact monoid audit removes the remaining mass-bound uncertainty status",
        ),
        "markdown_exposes_frontier": gate(
            "Batch-3 Branch-Closed Frontier" in md_text
            and "desired_q1_branches: `97`" in md_text
            and "viable_branches: `0`" in md_text,
            str(md_path),
            "markdown exposes batch3 branch-closed frontier totals",
        ),
    }
    return {
        "scope": "verification for batch3 branch-closed frontier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_batch3_branch_closed_frontier_verification.json"
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
