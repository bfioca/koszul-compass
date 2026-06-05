#!/usr/bin/env python3
"""Build a compact certificate for the current best CICY 7484 construction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def actual_pair_from_record(record: dict[str, Any]) -> list[int] | None:
    certificate = record["conditional_order4_descent_constraints"][
        "actual_z2xz2_wedge2_character_certificate"
    ]
    return certificate.get("per_character_pair") or certificate.get(
        "best_per_character_pair"
    )


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": status, "evidence": evidence, "note": note}


def build_certificate() -> dict[str, Any]:
    improved = load_json("k_even_improved_family.json")
    improved_family = improved["family"]
    best = next(
        record
        for record in improved["records"]
        if record["n"] == improved_family["best_n"]
    )
    spectrum = best["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    quality = best["cohomology_and_spectrum"]["line_bundle_sum_quality"]
    actual = best["actual_wedge2_character_certificate"]

    zero_full = load_json("cicy7484_kappa_plane_zero_allowed_bound8_kmax50.json")
    zero_high = load_json("cicy7484_kappa_zero_allowed_bound8_kmax80_skip50.json")
    regular_bound14 = load_json("cicy7484_selected_kappa_search_bound14.json")
    zero_selected_bound15 = load_json(
        "cicy7484_selected_kappa_zero_allowed_bound15.json"
    )
    pair_deformations = load_json("cicy7484_pair_deformations_delta12_n5.json")
    slope_5000 = load_json("gut_slope_checks_5000_adaptive.json")
    cohomology_5000 = load_json("gut_cohomology_smoke_5000_summary.json")

    zero_full_pairs = [actual_pair_from_record(record) for record in zero_full["records"]]
    zero_selected_bound15_pairs = [
        actual_pair_from_record(record) for record in zero_selected_bound15["records"]
    ]
    zero_full_best_records = [
        {
            "kappa_vector": record["kappa_vector"],
            "matrix": record["matrix"],
            "anomaly": record["anomaly"],
            "actual_pair": actual_pair_from_record(record),
            "trivial_summand_count": record["line_bundle_sum_quality"][
                "trivial_summand_count"
            ],
            "h0_v": record["line_bundle_sum_quality"]["h0_v"],
            "h0_v_dual": record["line_bundle_sum_quality"]["h0_v_dual"],
            "novel_combined": record["novelty"]["datasets"]["combined"][
                "novel_under_row_and_column_permutation"
            ],
        }
        for record in zero_full["records"]
        if actual_pair_from_record(record) == [6, 3]
    ]

    return {
        "scope": "current best certified-lift CICY 7484 line-bundle construction",
        "construction": {
            "label": "K_improved(-1)",
            "cicy": improved_family["cicy"],
            "symmetry_order": improved_family["symmetry_order"],
            "matrix": best["matrix"],
            "family_base_matrix": improved_family["base_matrix"],
            "family_direction": improved_family["direction"],
            "family_formula": improved_family["formula"],
            "family_parameter": "n = -1",
            "hard_gate_segment": improved_family["hard_gate_segment"],
            "exact_kappa_vector": improved_family["exact_kappa_vector"],
            "polynomial_certificates": improved_family["polynomial_certificates"],
        },
        "gate_checklist": {
            "c1_zero": gate(
                best["c1"] == [0, 0, 0],
                "reports/k_even_improved_family.json",
                f"c1(V)={best['c1']}",
            ),
            "index_chirality": gate(
                best["index_v"] == -12 and best["index_wedge2_v"] == -12,
                "reports/k_even_improved_family.json",
                f"ind(V)={best['index_v']}, ind(wedge^2 V)={best['index_wedge2_v']}",
            ),
            "anomaly_effective": gate(
                all(value >= 0 for value in best["anomaly"]),
                "reports/k_even_improved_family.json",
                f"ambient anomaly={best['anomaly']}",
            ),
            "slope_polystable": gate(
                best["passes_hard_gates"]
                and improved_family["exact_kappa_vector"] == [1, 3, 5],
                "reports/k_even_improved_family.json",
                "exact kappa=(1,3,5) ray; direct sum of slope-zero line bundles",
            ),
            "cohomology_spectrum": gate(
                spectrum["upstairs_10"] == 12
                and spectrum["upstairs_anti_10"] == 0
                and spectrum["upstairs_5bar"] == 24
                and spectrum["upstairs_5"] == 12,
                "reports/k_even_improved_family.json",
                (
                    f"upstairs 10/anti10/5bar/5="
                    f"{spectrum['upstairs_10']}/{spectrum['upstairs_anti_10']}/"
                    f"{spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}"
                ),
            ),
            "raw_z2xz2_lift": gate(
                best["raw_symmetry_diagnostic"][
                    "equivariant_line_bundle_sum_lift_exists"
                ],
                "reports/k_even_improved_family.json",
                "raw free Z2xZ2 line-bundle-sum lift exists",
            ),
            "actual_wilson_line_character": gate(
                actual["character_computed"]
                and actual["best_per_character_pair"] == [6, 3],
                "reports/k_even_improved_family.json",
                "actual downstairs per-character (5bar,5)=(6,3)",
            ),
            "implemented_novelty": gate(
                best["novelty"]["datasets"]["combined"][
                    "novel_under_row_and_column_permutation"
                ],
                "reports/k_even_improved_family.json",
                "novel under implemented GUTall+sms202 row/column equivalences",
            ),
        },
        "spectrum": {
            "upstairs_10": spectrum["upstairs_10"],
            "upstairs_anti_10": spectrum["upstairs_anti_10"],
            "upstairs_5bar": spectrum["upstairs_5bar"],
            "upstairs_5": spectrum["upstairs_5"],
            "actual_per_character_pair": actual["best_per_character_pair"],
            "actual_three_family_no_vectorlike_pair": actual[
                "actual_three_family_no_vectorlike_pair"
            ],
            "actual_mssm_one_higgs_pair_without_triplets": actual[
                "actual_mssm_one_higgs_pair_without_triplets"
            ],
        },
        "quality_caveat": {
            "trivial_summand_count": quality["trivial_summand_count"],
            "trivial_summand_indices": quality["trivial_summand_indices"],
            "h0_v": quality["h0_v"],
            "h0_v_dual": quality["h0_v_dual"],
            "regular_nontrivial_summand_scan_style": quality[
                "regular_nontrivial_summand_scan_style"
            ],
            "interpretation": quality["interpretation"],
        },
        "comparison_evidence": {
            "regular_nontrivial_selected_bound14": {
                "evidence": "reports/cicy7484_selected_kappa_search_bound14.json",
                "unique_zero_sum_multiset_count": regular_bound14["search"][
                    "unique_zero_sum_multiset_count"
                ],
                "spectrum_lift_count": regular_bound14["search"][
                    "spectrum_lift_count"
                ],
                "best_actual_pair": regular_bound14["search"]["best_actual_pair"],
                "all_records_regular_nontrivial": all(
                    record["line_bundle_sum_quality"][
                        "regular_nontrivial_summand_scan_style"
                    ]
                    for record in regular_bound14["records"]
                ),
            },
            "zero_allowed_full_bound8_kmax50": {
                "evidence": "reports/cicy7484_kappa_plane_zero_allowed_bound8_kmax50.json",
                "candidate_kappa_plane_count": zero_full["search"][
                    "candidate_kappa_plane_count"
                ],
                "unique_zero_sum_multiset_count": zero_full["search"][
                    "unique_zero_sum_multiset_count"
                ],
                "spectrum_lift_count": zero_full["search"]["spectrum_lift_count"],
                "best_actual_pair": zero_full["search"]["best_actual_pair"],
                "best_pair_record_count": zero_full_pairs.count([6, 3]),
                "best_pair_records": zero_full_best_records,
            },
            "zero_allowed_selected_bound15": {
                "evidence": "reports/cicy7484_selected_kappa_zero_allowed_bound15.json",
                "unique_zero_sum_multiset_count": zero_selected_bound15["search"][
                    "unique_zero_sum_multiset_count"
                ],
                "spectrum_lift_count": zero_selected_bound15["search"][
                    "spectrum_lift_count"
                ],
                "best_actual_pair": zero_selected_bound15["search"][
                    "best_actual_pair"
                ],
                "best_pair_record_count": zero_selected_bound15_pairs.count([6, 3]),
                "has_actual_three_family_no_vectorlike_pair": any(
                    record["conditional_order4_descent_constraints"][
                        "actual_z2xz2_wedge2_character_certificate"
                    ]["actual_three_family_no_vectorlike_pair"]
                    for record in zero_selected_bound15["records"]
                ),
                "has_actual_one_higgs_pair_without_triplets": any(
                    record["conditional_order4_descent_constraints"][
                        "actual_z2xz2_wedge2_character_certificate"
                    ]["actual_mssm_one_higgs_pair_without_triplets"]
                    for record in zero_selected_bound15["records"]
                ),
            },
            "zero_allowed_high_kappa_bound8_skip50": {
                "evidence": "reports/cicy7484_kappa_zero_allowed_bound8_kmax80_skip50.json",
                "candidate_kappa_plane_count": zero_high["search"][
                    "candidate_kappa_plane_count"
                ],
                "unique_zero_sum_multiset_count": zero_high["search"][
                    "unique_zero_sum_multiset_count"
                ],
                "algebraic_survivor_count": zero_high["search"][
                    "algebraic_survivor_count"
                ],
            },
            "local_pair_deformations": {
                "evidence": "reports/cicy7484_pair_deformations_delta12_n5.json",
                "best_nontrivial_actual_pair": pair_deformations["search"][
                    "best_nontrivial_actual_pair"
                ],
                "best_zero_allowed_actual_pair": pair_deformations["search"][
                    "best_zero_allowed_actual_pair"
                ],
            },
            "benchmark_reproduction": {
                "algebraic_models_checked": 63325,
                "adaptive_slope_models_checked": slope_5000["checked_models"],
                "adaptive_slope_retry_count": slope_5000["retry_count"],
                "adaptive_slope_final_failures": len(slope_5000["failures"]),
                "pycicy_cohomology_models_checked": cohomology_5000[
                    "checked_models"
                ],
                "pycicy_cohomology_failures": cohomology_5000["failure_count"],
            },
        },
        "expert_review_items": [
            "Decide whether two trivial O_X summands are admissible for the intended structure-group and gauge-sector assumptions.",
            "Check novelty under divisor-basis automorphisms and line-bundle equivalences beyond implemented row/column canonicalization.",
            "Search for a regular nontrivial-summand certified candidate improving on actual (5bar,5)=(9,6), or an exact/near-MSSM actual Wilson-line spectrum.",
        ],
    }


def write_markdown(certificate: dict[str, Any], path: Path) -> None:
    construction = certificate["construction"]
    spectrum = certificate["spectrum"]
    caveat = certificate["quality_caveat"]
    lines = [
        "# Best Candidate Certificate",
        "",
        f"Label: `{construction['label']}` on CICY `{construction['cicy']}` with symmetry order `{construction['symmetry_order']}`.",
        "",
        "```text",
        str(construction["matrix"]),
        "```",
        "",
        "## Gates",
        "",
    ]
    for name, record in certificate["gate_checklist"].items():
        status = "PASS" if record["pass"] else "FAIL"
        lines.append(f"- `{name}`: {status}. {record['note']} ({record['evidence']})")
    lines.extend(
        [
            "",
            "## Spectrum",
            "",
            (
                f"Upstairs `10/anti10/5bar/5` = "
                f"`{spectrum['upstairs_10']}/{spectrum['upstairs_anti_10']}/"
                f"{spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}`."
            ),
            f"Actual downstairs per-character `(5bar,5)` = `{spectrum['actual_per_character_pair']}`.",
            f"Actual exact no-vectorlike `(3,0)`: `{spectrum['actual_three_family_no_vectorlike_pair']}`.",
            f"Actual one-Higgs-pair `(4,1)`: `{spectrum['actual_mssm_one_higgs_pair_without_triplets']}`.",
            "",
            "## Caveat",
            "",
            (
                f"Trivial summands: `{caveat['trivial_summand_count']}` at indices "
                f"`{caveat['trivial_summand_indices']}`; "
                f"`h0(V)={caveat['h0_v']}`, `h0(V*)={caveat['h0_v_dual']}`."
            ),
            caveat["interpretation"],
            "",
            "## Comparison Evidence",
            "",
        ]
    )
    for name, record in certificate["comparison_evidence"].items():
        summary = ", ".join(
            f"{key}={value}"
            for key, value in record.items()
            if key != "best_pair_records"
        )
        lines.append(f"- `{name}`: {summary}")
    lines.extend(["", "## Expert Review Items", ""])
    for item in certificate["expert_review_items"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "best_candidate_certificate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "best_candidate_certificate.md"),
    )
    args = parser.parse_args()

    certificate = build_certificate()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(certificate, md_out)
    print(f"label={certificate['construction']['label']}")
    print(f"actual_pair={certificate['spectrum']['actual_per_character_pair']}")
    print(f"trivial_summands={certificate['quality_caveat']['trivial_summand_count']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
