#!/usr/bin/env python3
"""Verify radius-5 window-3 large branch closure."""

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
    closure_json: Path,
    closure_md: Path,
    expected_total: int,
    expected_desired: int,
    expected_not_desired: int,
    expected_category: str,
) -> dict[str, Any]:
    path = closure_json
    md_path = closure_md
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    representative = report["q1_representative_candidate"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side radius5 window3 large branch gates passed",
        ),
        "large_branch_counts_match": gate(
            summary["total_branches"] == expected_total
            and summary["desired_q1_branches"] == expected_desired
            and summary["not_desired_q1_branches"] == expected_not_desired
            and summary["q1_support_signature_count"] == 1
            and summary["viable_q1_branches"] == 0,
            str(path),
            "large branch aggregate counts match expected q1 support closure",
        ),
        "representative_has_required_tables": gate(
            representative is not None
            and representative["spectrum_certificate"]["desired_q1_three_family_signature"]
            and representative["character_certificate"]["character_certified"]
            and representative["mass_operator_table"] is not None
            and representative["proton_decay_operator_table"] is not None
            and representative["classification"]["category"] == expected_category,
            str(path),
            "support-invariant q1 representative has full tables and expected classification",
        ),
        "markdown_exposes_large_closure": gate(
            report.get("title", "Radius-5 Window 3 Large Branch Closure") in md_text
            and f"desired_q1_branches: `{expected_desired}`" in md_text
            and "viable_q1_branches: `0`" in md_text,
            str(md_path),
            "markdown exposes large branch closure totals",
        ),
    }
    return {
        "scope": "verification for radius5 window3 large branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--closure-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window3_large_branch_closure.json"),
    )
    parser.add_argument(
        "--closure-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window3_large_branch_closure.md"),
    )
    parser.add_argument("--expected-total", type=int, default=531441)
    parser.add_argument("--expected-desired", type=int, default=41553)
    parser.add_argument("--expected-not-desired", type=int, default=489888)
    parser.add_argument("--expected-category", default="phenomenologically obstructed")
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius5_window3_large_branch_closure_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(
        closure_json=Path(args.closure_json),
        closure_md=Path(args.closure_md),
        expected_total=args.expected_total,
        expected_desired=args.expected_desired,
        expected_not_desired=args.expected_not_desired,
        expected_category=args.expected_category,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
