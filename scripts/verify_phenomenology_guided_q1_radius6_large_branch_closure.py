#!/usr/bin/env python3
"""Verify a radius-6 large branch closure artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(
    *,
    closure_json: Path,
    closure_md: Path,
    expected_total: int | None,
    expected_desired: int | None,
) -> dict[str, Any]:
    report = load_json(closure_json)
    md_text = closure_md.read_text(encoding="utf-8")
    summary = report["summary"]
    representative = report["q1_representative_candidate"]
    has_representative_boundary = "representative_grammar_status" in summary
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(closure_json),
            "builder-side radius6 large branch gates passed",
        ),
        "large_branch_counts_consistent": gate(
            summary["total_branches"]
            == summary["desired_q1_branches"] + summary["not_desired_q1_branches"]
            and (expected_total is None or summary["total_branches"] == expected_total)
            and (expected_desired is None or summary["desired_q1_branches"] == expected_desired)
            and summary["q1_support_signature_count"] == 1
            and summary["viable_q1_branches"] == 0,
            str(closure_json),
            "large branch aggregate counts and support-invariant q1 closure are consistent",
        ),
        "representative_has_required_tables": gate(
            representative is not None
            and representative["spectrum_certificate"]["desired_q1_three_family_signature"]
            and representative["character_certificate"]["character_certified"]
            and representative["mass_operator_table"] is not None
            and representative["proton_decay_operator_table"] is not None
            and representative["classification"]["category"]
            in {"phenomenologically obstructed", "unresolved"},
            str(closure_json),
            "support-invariant q1 representative has full tables and non-viable classification",
        ),
        "representative_grammar_boundary_if_advertised": gate(
            not has_representative_boundary
            or (
                representative is not None
                and "representative_grammar_gate" in representative
                and "character_refined_classification" in representative
                and representative["representative_grammar_gate"][
                    "representative_grammar_stage"
                ]["status"]
                == summary["representative_grammar_status"]
                and summary["viable_q1_branches"]
                == summary["representative_grammar_promoted_q1_branches"]
                and summary["cup_product_eligible_q1_branches"] >= 0
            ),
            str(closure_json),
            "new large-branch closure artifacts expose representative grammar promotion/prune counts",
        ),
        "markdown_exposes_large_closure": gate(
            report["title"] in md_text
            and "desired_q1_branches" in md_text
            and "viable_q1_branches: `0`" in md_text,
            str(closure_md),
            "markdown exposes large branch closure totals",
        ),
    }
    return {
        "scope": "verification for radius6 large branch closure",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--closure-json", required=True)
    parser.add_argument("--closure-md", required=True)
    parser.add_argument("--expected-total", type=int, default=None)
    parser.add_argument("--expected-desired", type=int, default=None)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()
    result = verify(
        closure_json=Path(args.closure_json),
        closure_md=Path(args.closure_md),
        expected_total=args.expected_total,
        expected_desired=args.expected_desired,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
