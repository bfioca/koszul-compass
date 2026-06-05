#!/usr/bin/env python3
"""Verify the CICY 5259 split-lift report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_split_lift_report import build_report  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify() -> dict[str, Any]:
    path = REPORTS / "cicy5259_split_lift_report.json"
    md_path = REPORTS / "cicy5259_split_lift_report.md"
    report = load_json(path)
    rebuilt = build_report()

    cert = report["zero_extended_bundle_certificate"]
    split = report["ineffective_split_audit"]["selected_hit"]
    rebuilt_cert = rebuilt["zero_extended_bundle_certificate"]
    md_text = md_path.read_text(encoding="utf-8")

    gates = {
        "conclusion_records_split_lift_status": gate(
            report["conclusion"]["status"]
            == "full_upstairs_split_lift_certified__quotient_descent_blocked"
            and report["conclusion"]["missing_seventh_divisor_obtained"]
            and report["conclusion"]["full_upstairs_su5_line_bundle_certificate"]
            and not report["conclusion"]["full_quotient_wilson_line_certificate"],
            str(path),
            "report distinguishes full upstairs split-lift certification from blocked quotient descent",
        ),
        "selected_split_contracts_to_5259": gate(
            split["candidate_num"] == 7914
            and split["candidate_favourable"]
            and split["split_row_index"] == 6
            and split["split_columns"] == [0, 1, 2]
            and split["contracted_conf"] == report["cicy5259"]["conf"]
            and split["canonical_reconstructs_target"],
            str(path),
            "CICY 7914 is the explicit favourable P2 split whose contraction reproduces 5259",
        ),
        "full_picard_topology_rebuilt_matches_report": gate(
            rebuilt["full_picard_presentation_7914"]["c2_tx"]
            == report["full_picard_presentation_7914"]["c2_tx"]
            and rebuilt["full_picard_presentation_7914"]["intersection_tensor"]["sha256"]
            == report["full_picard_presentation_7914"]["intersection_tensor"]["sha256"]
            and report["full_picard_presentation_7914"]["metadata"]["h11"] == 7
            and report["full_picard_presentation_7914"]["metadata"][
                "num_projective_factors"
            ]
            == 7,
            str(path),
            "full favourable c2 and intersection tensor are reproducible",
        ),
        "zero_extended_topology_gates_match": gate(
            cert["c1"] == [0, 0, 0, 0, 0, 0, 0]
            and cert["index_v"] == -6
            and cert["index_wedge2_v"] == -6
            and cert["c2_v"] == [14, 8, 20, 12, 8, 34, 17]
            and cert["anomaly"] == [10, 16, 4, 12, 16, 22, 19]
            and rebuilt_cert["c2_v"] == cert["c2_v"]
            and rebuilt_cert["anomaly"] == cert["anomaly"],
            str(path),
            "zero-extended bundle has the expected full seven-component topology",
        ),
        "slope_and_cohomology_rebuilt_match": gate(
            cert["slope_search"]["feasible"]
            and cert["slope_search"]["max_normalized_slope"] <= 1e-7
            and rebuilt_cert["cohomology"] == cert["cohomology"]
            and cert["cohomology"]["V"] == [0, 6, 0, 0]
            and cert["cohomology"]["V_dual"] == [0, 0, 6, 0]
            and cert["cohomology"]["wedge2_V"] == [0, 16, 10, 0]
            and cert["cohomology"]["wedge2_V_dual"] == [0, 10, 16, 0],
            str(path),
            "full favourable slope and pyCICY cohomology gates are reproducible",
        ),
        "upstairs_spectrum_is_order_two_three_family": gate(
            cert["su5_upstairs_spectrum"]["expected_upstairs_chirality"] == 6
            and cert["su5_upstairs_spectrum"]["upstairs_10"] == 6
            and cert["su5_upstairs_spectrum"]["upstairs_anti_10"] == 0
            and cert["su5_upstairs_spectrum"]["upstairs_5bar"] == 16
            and cert["su5_upstairs_spectrum"]["upstairs_5"] == 10
            and all(cert["su5_upstairs_spectrum"]["checks"].values()),
            str(path),
            "upstairs order-two spectrum has three-family chirality and no anti-10s",
        ),
        "quotient_boundary_is_explicit": gate(
            report["full_picard_presentation_7914"]["metadata"]["symmetry_status"]
            == "unknown"
            and len(report["quotient_descent_boundary"]["blocked_items"]) == 4
            and report["gates"]["quotient_descent_still_blocked"]["pass"],
            str(path),
            "report records the missing split-compatible equivariant data",
        ),
        "markdown_matches_result": gate(
            "Status: `full_upstairs_split_lift_certified__quotient_descent_blocked`"
            in md_text
            and "Full upstairs SU(5) line-bundle certificate: yes" in md_text
            and "Full quotient/Wilson-line certificate: no" in md_text,
            str(md_path),
            "markdown memo exposes the split-lift result and remaining obstruction",
        ),
    }
    return {
        "scope": "verification for CICY5259 split-lift report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_split_lift_verification.json"),
    )
    args = parser.parse_args()

    result = verify()
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
