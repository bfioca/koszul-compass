#!/usr/bin/env python3
"""Verify aggregate closure of the large selected radius-4 branch."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_large_branch_closure.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_large_branch_closure.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    representative = report["q1_representative_candidate"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side large-branch closure gates passed",
        ),
        "full_branch_space_counted": gate(
            report["summary"]["total_branches"] == 531441
            and report["summary"]["desired_q1_branches"] == 41553
            and report["summary"]["not_desired_q1_branches"] == 489888,
            str(path),
            "large 12-block branch space is fully counted",
        ),
        "q1_support_invariant": gate(
            report["summary"]["q1_support_signature_count"] == 1
            and representative["radius4_large_branch_representative"][
                "support_invariant_across_q1_branches"
            ],
            str(path),
            "all desired-q1 branches have one charged-matter support signature",
        ),
        "representative_is_obstructed": gate(
            representative["spectrum_certificate"]["desired_q1_three_family_signature"]
            and representative["classification"]["category"]
            == "phenomenologically obstructed"
            and representative["classification"]["status"]
            == "dangerous_10_5bar_5bar_operator_allowed"
            and report["summary"]["viable_q1_branches"] == 0,
            str(path),
            "support-invariant q=1 representative is obstructed by dangerous operator",
        ),
        "representative_has_required_tables": gate(
            {
                "spectrum_certificate",
                "character_certificate",
                "mass_operator_table",
                "proton_decay_operator_table",
                "classification",
            }.issubset(representative)
            and representative["mass_operator_table"] is not None
            and representative["proton_decay_operator_table"] is not None,
            str(path),
            "q=1 representative emits required certificate tables",
        ),
        "markdown_exposes_summary": gate(
            "desired_q1_branches: `41553`" in md_text
            and "q1_representative_status: `dangerous_10_5bar_5bar_operator_allowed`"
            in md_text
            and "viable_q1_branches: `0`" in md_text,
            str(md_path),
            "markdown exposes large-branch closure summary",
        ),
    }
    return {
        "scope": "verification for selected radius-4 large branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_large_branch_closure_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
