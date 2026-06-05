#!/usr/bin/env python3
"""Verify the CICY 5259/7914 quotient Wilson-line report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import build_report  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify() -> dict[str, Any]:
    path = REPORTS / "cicy5259_quotient_wilson_line_report.json"
    md_path = REPORTS / "cicy5259_quotient_wilson_line_report.md"
    report = load_json(path)
    rebuilt = build_report()
    md_text = md_path.read_text(encoding="utf-8")

    sectors = report["equivariant_cohomology_characters"]
    rebuilt_sectors = rebuilt["equivariant_cohomology_characters"]
    wilson = report["wilson_line_enumeration"]["admissible_nontrivial_embeddings"][0]
    five = wilson["fivebar_and_five_sector"]
    mixed = next(
        cert
        for cert in sectors["wedge2_V"]["line_certificates"]
        if cert["line_bundle"] == [1, -2, 0, 1, 2, -1, 0]
    )
    mixed_dual = next(
        cert
        for cert in sectors["wedge2_V_dual"]["line_certificates"]
        if cert["line_bundle"] == [-1, 2, 0, -1, -2, 1, 0]
    )

    gates = {
        "conclusion_records_final_obstruction": gate(
            report["conclusion"]["status"]
            == "quotient_lift_certified__wilson_line_rejected_excess_vectorlike_5_content"
            and report["conclusion"]["split_action_lift_certified"]
            and report["conclusion"]["full_picard_action_certified"]
            and report["conclusion"]["line_bundle_equivariance_certified"]
            and report["conclusion"]["cohomology_characters_computed"]
            and not report["conclusion"]["standard_model_like_candidate_certified"]
            and report["conclusion"]["precise_obstruction"]
            == "excessive_vectorlike_5_content",
            str(path),
            "report records a successful quotient/equivariant lift and the final vectorlike-content obstruction",
        ),
        "selected_action_and_split_lift_match": gate(
            report["selected_recorded_free_action_5259"]["option_index"] == 0
            and report["selected_recorded_free_action_5259"]["ambient_row_permutation"]
            == [0, 1, 2, 3, 4, 5]
            and report["split_lift_7914"]["p2_coordinate_signs"] == [1, -1, 1]
            and report["split_lift_7914"]["split_equation_signs"] == [1, -1, 1]
            and report["split_lift_7914"]["equation_signs_7914"]
            == [1, -1, 1, 1, -1, 1, 1]
            and report["split_lift_7914"]["induced_picard_action_on_J0_to_J6"]
            == [0, 1, 2, 3, 4, 5, 6]
            and report["split_lift_7914"]["matches_original_first_polynomial_sign"],
            str(path),
            "selected 5259 option 0 and balanced 7914 P2 lift are recorded exactly",
        ),
        "line_bundle_equivariance_certified": gate(
            report["line_bundle_equivariance"]["determinant_fiber_sign"] == 1
            and report["line_bundle_equivariance"][
                "admissible_determinant_trivial_fiber_lift_count"
            ]
            == 16
            and report["line_bundle_equivariance"]["all_summand_divisor_classes_fixed"]
            and report["line_bundle_equivariance"]["direct_sum_equivariant_lift_exists"],
            str(path),
            "zero-extended summands are fixed and determinant-trivial Z2 linearisations exist",
        ),
        "characters_match_rebuild_and_expected_regularities": gate(
            sectors["V"]["cohomology_characters"]
            == rebuilt_sectors["V"]["cohomology_characters"]
            and sectors["wedge2_V"]["cohomology_characters"]
            == rebuilt_sectors["wedge2_V"]["cohomology_characters"]
            and sectors["V"]["cohomology_characters"]["H1"]["multiplicities"]
            == {"+": 3, "-": 3}
            and sectors["wedge2_V"]["cohomology_characters"]["H1"][
                "multiplicities"
            ]
            == {"+": 8, "-": 8}
            and sectors["wedge2_V"]["cohomology_characters"]["H2"][
                "multiplicities"
            ]
            == {"+": 5, "-": 5}
            and sectors["wedge2_V_dual"]["cohomology_characters"]["H1"][
                "multiplicities"
            ]
            == {"+": 5, "-": 5},
            str(path),
            "actual Z2 cohomology characters are regular and reproducible",
        ),
        "mixed_koszul_certificates_resolve_vectorlike_sector": gate(
            mixed["method"] == "two_term_koszul_map_injective_by_pycicy_dimension"
            and mixed["actual"]["H1"]["multiplicities"] == {"+": 3, "-": 3}
            and mixed["actual"]["H2"]["multiplicities"] == {"+": 4, "-": 4}
            and mixed_dual["method"]
            == "two_term_koszul_map_surjective_by_pycicy_dimension"
            and mixed_dual["actual"]["H1"]["multiplicities"] == {"+": 4, "-": 4}
            and mixed_dual["actual"]["H2"]["multiplicities"] == {"+": 3, "-": 3},
            str(path),
            "the only mixed line summands have resolved Koszul source-character certificates",
        ),
        "wilson_line_spectrum_is_not_sm_like": gate(
            wilson["ten_sector"]["three_family_10_sector"]
            and five["net_dbar_families"] == 3
            and five["net_lepton_doublet_families"] == 3
            and five["colored_triplet_vectorlike_pairs"] == 5
            and five["electroweak_doublet_vectorlike_pairs"] == 5
            and not wilson["standard_model_like"]
            and wilson["obstruction"] == "excessive_vectorlike_5_content",
            str(path),
            "nontrivial Z2 Wilson line gives three-family chirality plus five vectorlike 5+5bar pairs",
        ),
        "markdown_matches_report": gate(
            "Status: `quotient_lift_certified__wilson_line_rejected_excess_vectorlike_5_content`"
            in md_text
            and "colored triplet vectorlike pairs: `5`" in md_text
            and "electroweak doublet vectorlike pairs: `5`" in md_text,
            str(md_path),
            "markdown memo exposes the final obstruction",
        ),
    }
    return {
        "scope": "verification for CICY5259 quotient/Wilson-line report",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_quotient_wilson_line_verification.json"),
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
