#!/usr/bin/env python3
"""Verify exact monoid audit for batch-3 branch mass-bound q=1 candidates."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_mass_monoid_audit.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_batch3_branch_mass_monoid_audit.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side batch-3 branch mass audit gates passed",
        ),
        "all_branch_mass_rows_upgraded": gate(
            report["summary"] == {
                "mass_bound_branches": 2,
                "open_mass_bound_uncertainties": 0,
                "upgraded_obstructions": 2,
            }
            and all(
                candidate["all_mass_entries_monoid_obstructed"]
                for candidate in report["audited_candidates"]
            ),
            str(path),
            "all mass-bound q=1 branches are exact monoid obstructions",
        ),
        "markdown_exposes_upgrade": gate(
            "upgraded_obstructions: `2`" in md_text
            and "open_mass_bound_uncertainties: `0`" in md_text,
            str(md_path),
            "markdown exposes batch-3 branch mass-bound closure",
        ),
    }
    return {
        "scope": "verification for batch-3 branch mass monoid audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_batch3_branch_mass_monoid_audit_verification.json"
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
