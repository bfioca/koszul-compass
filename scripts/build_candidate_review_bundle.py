#!/usr/bin/env python3
"""Build compact review tables for the CICY 7484 candidate segment."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(name: str):
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def compact_matrix(matrix: list[list[int]]) -> str:
    return "; ".join("[" + ", ".join(str(x) for x in row) + "]" for row in matrix)


def build_rows() -> list[dict[str, object]]:
    family = load_json("family_candidate_7484_shift12.json")
    novelty = {record["n"]: record for record in load_json("candidate_novelty_7484_shift12.json")["records"]}
    equivariance = {
        record["n"]: record
        for record in load_json("candidate_equivariance_7484_shift12.json")["records"]
    }
    symbolic_slope = {
        record["n"]: record
        for record in load_json("symbolic_slope_7484_shift12.json")["records"]
    }

    rows: list[dict[str, object]] = []
    for record in family["records"]:
        n = record["n"]
        spectrum = record["su5_upstairs_spectrum"]
        descent = record["conditional_order4_descent_constraints"]
        z2xz2_envelope = descent.get("z2xz2_wilson_line_spectrum_envelope", {})
        combined_novelty = novelty[n]["datasets"]["combined"] if n in novelty else {}
        equivariance_options = {}
        if n in equivariance:
            equivariance_options = {
                option["label"]: option["line_bundle_sum_invariant_up_to_columns"]
                for option in equivariance[n]["equivariance_diagnostic"]["symmetry_options_from_cicylist"]
            }
            raw_topological = equivariance[n]["raw_symmetry_topological_diagnostic"]
        else:
            raw_topological = {}
        raw_lift_available = raw_topological.get("equivariant_line_bundle_sum_lift_exists")
        z2xz2_one_higgs = z2xz2_envelope.get(
            "allows_mssm_matter_plus_one_higgs_pair_without_colored_triplet_pairs"
        )
        z2xz2_chiral_no_pairs = z2xz2_envelope.get(
            "allows_exact_chiral_sm_matter_without_5_vectorlike_pairs"
        )
        rows.append(
            {
                "n": n,
                "matrix": compact_matrix(record["matrix"]),
                "passes_current_hard_gates": record["passes_current_hard_gates"],
                "novel_combined_row_column": combined_novelty.get(
                    "novel_under_row_and_column_permutation"
                ),
                "c1": record["c1"],
                "index_v": record["index_v"],
                "index_wedge2_v": record["index_wedge2_v"],
                "anomaly": record["anomaly"],
                "slope_feasible": record["slope_search"]["feasible"],
                "max_normalized_slope": record["slope_search"]["max_normalized_slope"],
                "slope_feasible_exact": symbolic_slope.get(n, {}).get("slope_feasible_exact"),
                "symbolic_slope_and_anomaly_pass": symbolic_slope.get(n, {}).get(
                    "symbolic_slope_and_anomaly_pass"
                ),
                "exact_polystable_and_anomaly_pass": symbolic_slope.get(n, {}).get(
                    "exact_polystable_and_anomaly_pass"
                ),
                "exact_kahler_ray": (
                    f"[1, 1, {symbolic_slope[n]['r_value']}]"
                    if n in symbolic_slope and symbolic_slope[n]["r_value"] is not None
                    else None
                ),
                "upstairs_10": spectrum["upstairs_10"],
                "upstairs_anti_10": spectrum["upstairs_anti_10"],
                "upstairs_5bar": spectrum["upstairs_5bar"],
                "upstairs_5": spectrum["upstairs_5"],
                "net_10_chirality": spectrum["net_10_chirality"],
                "net_5bar_chirality": spectrum["net_5bar_chirality"],
                "higgs_pair_candidates_upstairs": spectrum["higgs_pair_candidates_upstairs"],
                "order4_ten_forced_three_per_character": descent["checks"][
                    "ten_sector_forced_three_families_per_character"
                ],
                "order4_fivebar_net_three_per_character": descent["checks"][
                    "fivebar_sector_net_three_families_per_character"
                ],
                "order4_fivebar_representation_underdetermined": descent["fivebar_sector"][
                    "actual_representation_underdetermined"
                ],
                "z2xz2_allows_chiral_sm_no_5_pairs": z2xz2_chiral_no_pairs,
                "z2xz2_allows_one_higgs_pair_no_triplets": z2xz2_one_higgs,
                "z2xz2_raw_lift_available_for_envelope": raw_lift_available,
                "z2xz2_one_higgs_envelope_applicable_to_raw_symmetry": (
                    bool(raw_lift_available and z2xz2_one_higgs)
                    if raw_lift_available is not None and z2xz2_one_higgs is not None
                    else None
                ),
                "z2xz2_actual_wilson_line_spectrum_proven": z2xz2_envelope.get(
                    "actual_wilson_line_spectrum_proven"
                ),
                "full_wilson_line_spectrum_proven": descent["full_wilson_line_spectrum_proven"],
                "identity_ambient_row_action_ok": equivariance_options.get(
                    "order_4_identity_ambient_rows"
                ),
                "row_swap_ambient_row_action_ok": equivariance_options.get(
                    "order_4_row_swap_ambient_rows"
                ),
                "raw_free_order4_topological_action_ok": raw_topological.get(
                    "has_compatible_free_order_four_topological_action"
                ),
                "raw_compatible_free_order4_option_indices": raw_topological.get(
                    "compatible_free_order_four_option_indices"
                ),
                "equivariant_line_bundle_sum_lift_exists": raw_topological.get(
                    "equivariant_line_bundle_sum_lift_exists"
                ),
                "wilson_line_representation_on_cohomology_proven": raw_topological.get(
                    "wilson_line_representation_on_cohomology_proven"
                ),
            }
        )
    return rows


def write_markdown(rows: list[dict[str, object]], path: Path) -> None:
    columns = [
        "n",
        "passes_current_hard_gates",
        "novel_combined_row_column",
        "anomaly",
        "symbolic_slope_and_anomaly_pass",
        "exact_polystable_and_anomaly_pass",
        "max_normalized_slope",
        "upstairs_10",
        "upstairs_anti_10",
        "upstairs_5bar",
        "upstairs_5",
        "order4_ten_forced_three_per_character",
        "order4_fivebar_net_three_per_character",
        "z2xz2_allows_chiral_sm_no_5_pairs",
        "z2xz2_allows_one_higgs_pair_no_triplets",
        "z2xz2_raw_lift_available_for_envelope",
        "z2xz2_one_higgs_envelope_applicable_to_raw_symmetry",
        "identity_ambient_row_action_ok",
        "row_swap_ambient_row_action_ok",
        "raw_free_order4_topological_action_ok",
        "raw_compatible_free_order4_option_indices",
        "equivariant_line_bundle_sum_lift_exists",
        "full_wilson_line_spectrum_proven",
        "wilson_line_representation_on_cohomology_proven",
    ]
    lines = [
        "# Candidate Review Table",
        "",
        "Compact evidence table for the CICY 7484 deformation candidate.",
        "",
        "|" + "|".join(columns) + "|",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("|" + "|".join(str(row[column]) for column in columns) + "|")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-out", default=str(REPORTS / "candidate_review_table.csv"))
    parser.add_argument("--json-out", default=str(REPORTS / "candidate_review_table.json"))
    parser.add_argument("--md-out", default=str(REPORTS / "candidate_review_table.md"))
    args = parser.parse_args()

    rows = build_rows()
    json_out = Path(args.json_out)
    csv_out = Path(args.csv_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    with csv_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_markdown(rows, md_out)

    passing = [row["n"] for row in rows if row["passes_current_hard_gates"]]
    novel = [
        row["n"]
        for row in rows
        if row["passes_current_hard_gates"] and row["novel_combined_row_column"]
    ]
    print(f"rows={len(rows)}")
    print(f"passing_hard_gates={passing}")
    print(f"passing_and_novel={novel}")
    print(f"json_out={json_out}")
    print(f"csv_out={csv_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
