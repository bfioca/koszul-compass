#!/usr/bin/env python3
"""Verify exact monoid audit for final radius-5 unresolved mass records."""

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


def verify(*, audit_json: Path, audit_md: Path) -> dict[str, Any]:
    report = load_json(audit_json)
    md_text = audit_md.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(audit_json),
            "builder-side unresolved mass monoid audit gates passed",
        ),
        "all_unresolved_weight_accounted": gate(
            summary["weighted_unresolved_q1_completions"] == 578
            and summary["direct_scout_records"] == 4
            and summary["bounded_branch_records"] == 70
            and summary["large_branch_representatives"] == 1,
            str(audit_json),
            "audit accounts for all final aggregate no-certified-triplet-mass completions",
        ),
        "all_upgraded_to_monoid_obstruction": gate(
            summary["weighted_upgraded_monoid_obstructions"] == 578
            and summary["weighted_open_monoid_solutions"] == 0
            and summary["representatives_with_exact_monoid_solution"] == 0,
            str(audit_json),
            "every unresolved mass representative is exact certified-singlet monoid obstructed",
        ),
        "markdown_exposes_audit": gate(
            "weighted_unresolved_q1_completions: `578`" in md_text
            and "weighted_open_monoid_solutions: `0`" in md_text
            and "Open Representatives" in md_text,
            str(audit_md),
            "markdown exposes unresolved mass monoid audit totals",
        ),
    }
    return {
        "scope": "verification for final radius5 unresolved mass monoid audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--audit-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_unresolved_mass_monoid_audit.json"),
    )
    parser.add_argument(
        "--audit-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_unresolved_mass_monoid_audit.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius5_unresolved_mass_monoid_audit_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(audit_json=Path(args.audit_json), audit_md=Path(args.audit_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
