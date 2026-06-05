#!/usr/bin/env python3
"""Verify the comparative vectorlike 5/5bar obstruction report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_vectorlike_obstruction_report import build_report  # noqa: E402


EXPECTED_NEW_MATRIX = [
    [0, 1, 0, 0, -1],
    [-1, -1, 1, 0, 1],
    [0, 1, 0, -1, 0],
    [0, 1, -1, -1, 1],
    [1, 1, 0, -1, -1],
    [0, -1, 0, 1, 0],
    [0, 0, 0, 0, 0],
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify() -> dict[str, Any]:
    path = REPORTS / "vectorlike_obstruction_report.json"
    md_path = REPORTS / "vectorlike_obstruction_report.md"
    report = load_json(path)
    rebuilt = build_report()
    md_text = md_path.read_text(encoding="utf-8")

    new = report["new_5259_7914_candidate"]
    rebuilt_new = rebuilt["new_5259_7914_candidate"]
    prediction = new["vectorlike_pair_prediction"]
    local = report["local_5259_one_move_search"]
    summary_7484 = report["cicy7484_character_certified_summary"]
    gates = report["gates"]

    wedge_h1 = new["characters"]["wedge2_V"]["cohomology_characters"]["H1"]
    wedge_h2 = new["characters"]["wedge2_V"]["cohomology_characters"]["H2"]
    wedge_dual_h1 = new["characters"]["wedge2_V_dual"]["cohomology_characters"]["H1"]
    v_h1 = new["characters"]["V"]["cohomology_characters"]["H1"]

    comparison_pairs = [
        item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
        for item in report["comparative_records"]
        if item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
        is not None
    ]

    verification_gates = {
        "conclusion_records_new_lower_vectorlike_candidate": gate(
            report["conclusion"]["status"]
            == "new_5259_7914_deformation_reduces_vectorlike_pairs_to_three"
            and report["conclusion"]["new_candidate_found"]
            and report["conclusion"]["best_vectorlike_pair_count"] == 3
            and report["conclusion"]["best_record_label"] == "one_move_candidate",
            str(path),
            "report conclusion records the certified one-move reduction from five to three vectorlike pairs",
        ),
        "rebuilt_report_matches_persisted_new_candidate": gate(
            rebuilt_new["matrix"] == new["matrix"]
            and rebuilt_new["cohomology"] == new["cohomology"]
            and rebuilt_new["anomaly"] == new["anomaly"]
            and rebuilt_new["characters"] == new["characters"]
            and rebuilt["conclusion"] == report["conclusion"],
            str(path),
            "report rebuild reproduces the stored new 5259/7914 candidate and conclusion",
        ),
        "new_candidate_topology_and_spectrum_match_expected": gate(
            new["matrix"] == EXPECTED_NEW_MATRIX
            and new["move_from_base"] == [[2, 0, 2, 1]]
            and new["c1"] == [0, 0, 0, 0, 0, 0, 0]
            and new["index_v"] == -6
            and new["index_wedge2_v"] == -6
            and new["c2_v"] == [14, 4, 20, 14, 10, 30, 19]
            and new["anomaly"] == [10, 20, 4, 10, 14, 26, 17]
            and new["slope_search"]["feasible"]
            and new["slope_search"]["max_normalized_slope"] <= 1e-7
            and new["cohomology"]["V"] == [0, 6, 0, 0]
            and new["cohomology"]["V_dual"] == [0, 0, 6, 0]
            and new["cohomology"]["wedge2_V"] == [0, 12, 6, 0]
            and new["cohomology"]["wedge2_V_dual"] == [0, 6, 12, 0],
            str(path),
            "new one-move candidate preserves index, positive anomaly, slope feasibility, and the expected upstairs cohomology",
        ),
        "new_candidate_quality_gates_hold": gate(
            new["line_bundle_sum_quality"]["regular_nontrivial_summand_scan_style"]
            and new["su5_upstairs_spectrum"]["upstairs_10"] == 6
            and new["su5_upstairs_spectrum"]["upstairs_anti_10"] == 0
            and new["su5_upstairs_spectrum"]["upstairs_5bar"] == 12
            and new["su5_upstairs_spectrum"]["upstairs_5"] == 6
            and all(new["su5_upstairs_spectrum"]["checks"].values()),
            str(path),
            "candidate keeps the order-two three-family SU(5) gates with no anti-10s",
        ),
        "new_candidate_characters_are_regular": gate(
            new["character_certified"]
            and v_h1["multiplicities"] == {"+": 3, "-": 3}
            and wedge_h1["regular_multiplicity"] == 6
            and wedge_h1["multiplicities"] == {"+": 6, "-": 6}
            and wedge_h2["regular_multiplicity"] == 3
            and wedge_h2["multiplicities"] == {"+": 3, "-": 3}
            and wedge_dual_h1["regular_multiplicity"] == 3
            and wedge_dual_h1["multiplicities"] == {"+": 3, "-": 3},
            str(path),
            "Z2 equivariant cohomology characters are fully computed and regular for the new vectorlike sector",
        ),
        "wilson_line_vectorlike_count_follows_h2_regular_multiplicity": gate(
            prediction["regular_character_rule_applies"]
            and prediction["h1_wedge2_regular_multiplicity"] == 6
            and prediction["h2_wedge2_regular_multiplicity"] == 3
            and prediction["colored_triplet_vectorlike_pairs"] == 3
            and prediction["electroweak_doublet_vectorlike_pairs"] == 3
            and prediction["net_families"] == 3,
            str(path),
            "actual Wilson-line vectorlike count is the H2(wedge2 V) regular multiplicity",
        ),
        "bounded_search_and_7484_benchmarks_loaded": gate(
            local["counters"]["unique_candidates"] == 141
            and local["counters"]["topology_survivors"] == 32
            and local["counters"]["slope_survivors"] == 6
            and local["counters"]["spectrum_survivors"] == 6
            and local["counters"]["character_certified_survivors"] == 1
            and local["best_character_certified"]["matrix"] == EXPECTED_NEW_MATRIX
            and summary_7484["no_zero_count"] == 4
            and summary_7484["zero_allowed_count"] == 16
            and summary_7484["no_zero_best"]["vectorlike_pair_prediction"][
                "colored_triplet_vectorlike_pairs"
            ]
            == 6
            and summary_7484["zero_allowed_best"]["vectorlike_pair_prediction"][
                "colored_triplet_vectorlike_pairs"
            ]
            == 3,
            str(path),
            "bounded 5259 one-move search and both 7484 character-certified benchmark pools are represented",
        ),
        "comparative_gates_and_minimum_are_consistent": gate(
            all(item["pass"] for item in gates.values())
            and min(comparison_pairs) == 3
            and report["comparative_records"][0]["vectorlike_pair_prediction"][
                "colored_triplet_vectorlike_pairs"
            ]
            == 3,
            str(path),
            "comparative gates pass and no included certified record has fewer than three vectorlike pairs",
        ),
        "markdown_matches_report": gate(
            "Status: `new_5259_7914_deformation_reduces_vectorlike_pairs_to_three`"
            in md_text
            and "from `5` pairs to `3` pairs" in md_text
            and "vectorlike colored/electroweak pairs: `3` / `3`" in md_text
            and "minimum certified vectorlike count is three pairs" in md_text,
            str(md_path),
            "markdown memo exposes the new candidate and bounded obstruction statement",
        ),
    }
    return {
        "scope": "verification for vectorlike 5/5bar obstruction report",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "vectorlike_obstruction_verification.json"),
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
