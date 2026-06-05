#!/usr/bin/env python3
"""Verify the radius-6 DT-targeted exact mass monoid audit."""

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


def verify(
    *,
    audit_json: Path,
    audit_md: Path,
    branch_json: Path,
    scout_json: Path,
) -> dict[str, Any]:
    audit = load_json(audit_json)
    branch = load_json(branch_json)
    scout = load_json(scout_json)
    md_text = audit_md.read_text(encoding="utf-8")
    summary = audit["summary"]
    expected_direct = scout["summary"]["statuses"].get(
        "no_certified_triplet_mass_operator_found", 0
    )
    expected_branch = branch["summary"]["statuses"].get(
        "no_certified_triplet_mass_operator_found", 0
    )
    expected_total = expected_direct + expected_branch
    gates = {
        "builder_gates_pass": gate(
            audit["all_gates_pass"],
            str(audit_json),
            "builder-side radius6 mass monoid audit gates passed",
        ),
        "all_mass_unresolved_records_accounted": gate(
            summary["audited_records"] == expected_total
            and summary["direct_scout_records"] == expected_direct
            and summary["branch_records"] == expected_branch,
            str(audit_json),
            "audit accounts for all direct and branch radius6 no-certified-triplet-mass records",
        ),
        "all_upgraded_to_monoid_obstruction": gate(
            summary["upgraded_monoid_obstructions"] == expected_total
            and summary["open_exact_monoid_solutions"] == 0
            and summary["records_with_exact_monoid_solution"] == 0,
            str(audit_json),
            "every audited radius6 mass-unresolved record is exact singlet-monoid obstructed",
        ),
        "audited_records_have_solver_evidence": gate(
            all(
                item["mass_entries"]
                and all("exact_solution" in entry for entry in item["mass_entries"])
                for item in audit["audited_records"]
            ),
            str(audit_json),
            "all audited mass entries include exact solver evidence",
        ),
        "markdown_exposes_audit": gate(
            "Radius-6 DT Mass Monoid Audit" in md_text
            and "open_exact_monoid_solutions: `0`" in md_text
            and "Open Records" in md_text,
            str(audit_md),
            "markdown exposes radius6 mass monoid audit totals",
        ),
    }
    return {
        "scope": "verification for radius6 DT-targeted exact mass monoid audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--audit-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_mass_monoid_audit.json"),
    )
    parser.add_argument(
        "--audit-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_mass_monoid_audit.md"),
    )
    parser.add_argument(
        "--branch-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_branch_analysis.json"),
    )
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_mass_monoid_audit_verification.json"),
    )
    args = parser.parse_args()
    result = verify(
        audit_json=Path(args.audit_json),
        audit_md=Path(args.audit_md),
        branch_json=Path(args.branch_json),
        scout_json=Path(args.scout_json),
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
