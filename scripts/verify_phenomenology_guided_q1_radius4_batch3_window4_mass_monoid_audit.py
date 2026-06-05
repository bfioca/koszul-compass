#!/usr/bin/env python3
"""Verify batch-3 window-4 exact mass monoid audit."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_batch3_window4_mass_monoid_audit.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_batch3_window4_mass_monoid_audit.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    candidates = report["audited_candidates"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side mass monoid audit gates passed",
        ),
        "all_four_rows_upgraded": gate(
            report["summary"] == {
                "mass_bound_rows": 4,
                "open_mass_bound_uncertainties": 0,
                "upgraded_obstructions": 4,
            }
            and len(candidates) == 4
            and all(item["all_mass_entries_monoid_obstructed"] for item in candidates),
            str(path),
            "all four mass-bound rows are exact singlet-monoid obstructions",
        ),
        "solutions_show_no_nonnegative_monoid": gate(
            all(
                not entry["exact_solution"]["has_nonnegative_integer_solution"]
                for candidate in candidates
                for entry in candidate["mass_entries"]
            ),
            str(path),
            "every candidate triplet mass entry lacks a nonnegative certified-singlet solution",
        ),
        "markdown_exposes_upgrade": gate(
            "upgraded_obstructions: `4`" in md_text
            and "open_mass_bound_uncertainties: `0`" in md_text,
            str(md_path),
            "markdown exposes the mass-bound upgrade",
        ),
    }
    return {
        "scope": "verification for batch-3 window-4 mass monoid audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_batch3_window4_mass_monoid_audit_verification.json"
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
