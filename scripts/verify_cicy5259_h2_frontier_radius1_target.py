#!/usr/bin/env python3
"""Verify the radius-1 5259/7914 H2(wedge2 V) frontier target report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


EXPECTED_TARGET_MATRIX = [
    [-1, 1, 1, 0, -1],
    [0, -1, 0, 0, 1],
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
    path = REPORTS / "cicy5259_h2_frontier_radius1_target.json"
    md_path = REPORTS / "cicy5259_h2_frontier_radius1_target.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    best = report["best_character_certified_record"]
    prediction = best["vectorlike_pair_prediction"]
    counters = report["counters_by_radius"]
    target_records = report["target_records"]
    gates = report["gates"]

    wedge_h1 = best["characters"]["wedge2_V"]["cohomology_characters"]["H1"]
    wedge_h2 = best["characters"]["wedge2_V"]["cohomology_characters"]["H2"]
    wedge_dual_h1 = best["characters"]["wedge2_V_dual"]["cohomology_characters"]["H1"]
    v_h1 = best["characters"]["V"]["cohomology_characters"]["H1"]

    verification_gates = {
        "conclusion_records_q1_target": gate(
            report["conclusion"]["status"]
            == "target_found_h2_regular_multiplicity_le_one"
            and report["conclusion"]["target_found"]
            and report["conclusion"]["best_h2_regular_multiplicity"] == 1
            and report["conclusion"]["best_raw_h2_wedge2_v_after_spectrum"] == 2,
            str(path),
            "radius-1 frontier records a character-certified q=1 target",
        ),
        "move_families_and_counts_are_recorded": gate(
            report["move_families"]["single_column_row_dipole"][
                "raw_primitive_count"
            ]
            == 210
            and report["move_families"]["single_column_row_dipole"][
                "c1_preserving_as_one_step_count"
            ]
            == 0
            and report["move_families"]["two_column_row_transfer"][
                "primitive_count"
            ]
            == 140
            and report["move_families"]["paired_row_column_rectangle"][
                "primitive_count"
            ]
            == 420,
            str(path),
            "single-column dipoles, two-column row transfers, and paired row/column rectangles are accounted for",
        ),
        "frontier_gate_counts_match": gate(
            counters["0"]["unique_candidates"] == 1
            and counters["0"]["character_certified_survivors"] == 1
            and counters["1"]["unique_candidates"] == 558
            and counters["1"]["index_survivors"] == 122
            and counters["1"]["anomaly_survivors"] == 107
            and counters["1"]["slope_survivors"] == 53
            and counters["1"]["spectrum_survivors"] == 30
            and counters["1"]["character_certified_survivors"] == 5
            and report["certification_queue_size"] == 9,
            str(path),
            "bounded radius-1 candidate and survivor counts are stable",
        ),
        "raw_z2_lift_gate_passes": gate(
            report["raw_z2_lift_compatibility"]["split_action_lift_certified"]
            and report["raw_z2_lift_compatibility"]["full_picard_action"]
            == [0, 1, 2, 3, 4, 5, 6]
            and report["raw_z2_lift_compatibility"][
                "direct_sum_equivariant_lift_exists_for_starting_certificate"
            ]
            and gates["raw_z2_split_lift_compatibility_retained"]["pass"],
            str(path),
            "the selected Z2 split lift still fixes the full 7914 Picard basis",
        ),
        "best_target_topology_and_spectrum_match_expected": gate(
            best["matrix"] == EXPECTED_TARGET_MATRIX
            and best["frontier_radius"] == 1
            and best["frontier_move_families"] == {
                "paired_row_column_rectangle": 1
            }
            and best["move_from_base"]
            == [
                {
                    "columns": [0, 2],
                    "delta": -1,
                    "family": "paired_row_column_rectangle",
                    "rows": [0, 1],
                }
            ]
            and best["c1"] == [0, 0, 0, 0, 0, 0, 0]
            and best["index_v"] == -6
            and best["index_wedge2_v"] == -6
            and best["anomaly"] == [14, 16, 4, 12, 16, 26, 21]
            and best["slope_search"]["feasible"]
            and best["slope_search"]["max_normalized_slope"] <= 1e-7
            and best["cohomology"]["V"] == [0, 6, 0, 0]
            and best["cohomology"]["V_dual"] == [0, 0, 6, 0]
            and best["cohomology"]["wedge2_V"] == [0, 8, 2, 0]
            and best["cohomology"]["wedge2_V_dual"] == [0, 2, 8, 0]
            and best["su5_upstairs_spectrum"]["upstairs_anti_10"] == 0
            and all(best["su5_upstairs_spectrum"]["checks"].values()),
            str(path),
            "best target preserves topology, anomaly, slope feasibility, no anti-10s, and three-family chirality",
        ),
        "best_target_characters_are_regular": gate(
            best["character_certified"]
            and v_h1["multiplicities"] == {"+": 3, "-": 3}
            and wedge_h1["regular_multiplicity"] == 4
            and wedge_h1["multiplicities"] == {"+": 4, "-": 4}
            and wedge_h2["regular_multiplicity"] == 1
            and wedge_h2["multiplicities"] == {"+": 1, "-": 1}
            and wedge_dual_h1["regular_multiplicity"] == 1
            and wedge_dual_h1["multiplicities"] == {"+": 1, "-": 1},
            str(path),
            "equivariant cohomology is character-certified and H2(wedge2 V) has one regular Z2 copy",
        ),
        "wilson_line_prediction_is_one_vectorlike_pair": gate(
            prediction["regular_character_rule_applies"]
            and prediction["h1_wedge2_regular_multiplicity"] == 4
            and prediction["h2_wedge2_regular_multiplicity"] == 1
            and prediction["colored_triplet_vectorlike_pairs"] == 1
            and prediction["electroweak_doublet_vectorlike_pairs"] == 1
            and prediction["net_families"] == 3
            and len(target_records) == 1,
            str(path),
            "the certified regular-character rule predicts one vectorlike 5/5bar pair",
        ),
        "markdown_matches_report": gate(
            "Status: `target_found_h2_regular_multiplicity_le_one`" in md_text
            and "character-certified H2 regular multiplicity minimum: `1`"
            in md_text
            and "colored_triplet_vectorlike_pairs': 1" in md_text
            and "electroweak_doublet_vectorlike_pairs': 1" in md_text,
            str(md_path),
            "markdown exposes the q=1 target result",
        ),
    }
    return {
        "scope": "verification for CICY5259/7914 radius-1 H2 frontier target",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_h2_frontier_radius1_target_verification.json"),
    )
    args = parser.parse_args()

    result = verify()
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
