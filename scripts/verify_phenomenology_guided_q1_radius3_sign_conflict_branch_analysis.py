#!/usr/bin/env python3
"""Verify the radius-3 sign-conflict branch analysis."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    branches = report["branch_certificates"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side sign-conflict branch gates passed",
        ),
        "two_branches_emitted": gate(
            len(branches) == 2
            and all(record["character_certificate"]["character_certified"] for record in branches),
            str(path),
            "both character branches are emitted with complete certificates",
        ),
        "regular_branch_obstructed": gate(
            branches[0]["spectrum_certificate"]["desired_q1_three_family_signature"]
            and branches[0]["classification"]["category"] == "phenomenologically obstructed",
            str(path),
            "the desired-q1 branch is phenomenologically obstructed",
        ),
        "nonregular_branch_rejected": gate(
            not branches[1]["spectrum_certificate"]["desired_q1_three_family_signature"]
            and branches[1]["classification"]["status"]
            == "rejected_spectrum_signature_not_q1_three_family",
            str(path),
            "the nonregular branch is rejected as non-q1",
        ),
        "markdown_exposes_summary": gate(
            "Status: `sign_conflict_branches_nonviable_under_current_filter`" in md_text
            and "Branches" in md_text,
            str(md_path),
            "markdown exposes sign-conflict branch summary",
        ),
    }
    return {
        "scope": "verification for radius-3 sign-conflict branch analysis",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
