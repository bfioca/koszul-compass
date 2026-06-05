#!/usr/bin/env python3
"""Package the current line-bundle search state as a definite result stack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def all_pass(mapping: dict[str, Any]) -> bool:
    return all(item["pass"] for item in mapping.values())


def verification_summary() -> dict[str, Any]:
    final = load_json("final_deliverable_verification.json")
    favourable_no_go = load_json("outside_regime_free_symmetry_no_go_verification.json")
    nonfav = load_json("nonfavourable_extension_report_verification.json")
    cicy5259 = load_json("cicy5259_certifiability_upgrade_verification.json")
    return {
        "final_deliverable_verification": final["all_gates_pass"],
        "favourable_free_no_go_verification": favourable_no_go["all_gates_pass"],
        "nonfavourable_extension_verification": nonfav["all_gates_pass"],
        "cicy5259_certifiability_verification": cicy5259["all_gates_pass"],
        "all_current_stack_verifiers_pass": all(
            [
                final["all_gates_pass"],
                favourable_no_go["all_gates_pass"],
                nonfav["all_gates_pass"],
                cicy5259["all_gates_pass"],
            ]
        ),
    }


def build_package() -> dict[str, Any]:
    dataset = load_json("dataset_summary.json")
    final = load_json("final_deliverable_verification.json")
    cicy2544 = load_json("outside_regime_higgs_candidate_certificate.json")
    deformation = load_json("outside_regime_higgs_deformation_line.json")
    favourable_no_go = load_json("outside_regime_free_symmetry_no_go.json")
    cicy7484 = load_json("best_candidate_certificate.json")
    nonfav = load_json("nonfavourable_extension_report.json")
    cicy5259 = load_json("cicy5259_certifiability_upgrade_report.json")
    slope = load_json("gut_slope_checks_5000_adaptive.json")
    cohom = load_json("gut_cohomology_smoke_5000_summary.json")

    result_stack = [
        {
            "id": "benchmark_reproduction",
            "title": "Benchmark reproduction",
            "status": "verified",
            "claim": "Oxford SU(5) line-bundle algebraic, slope, and pyCICY smoke gates were reproduced in the current verifier stack.",
            "evidence": [
                "reports/dataset_summary.json",
                "reports/gut_benchmark_checks.json",
                "reports/gut_slope_checks_5000_adaptive.json",
                "reports/gut_cohomology_smoke_5000_summary.json",
                "reports/final_deliverable_verification.json",
            ],
            "key_numbers": {
                "GUTall_models": dataset["gutall"]["gut_model_count"],
                "sms202_models": dataset["sms202"]["model_count"],
                "adaptive_slope_models_checked": slope["checked_models"],
                "adaptive_slope_failures": len(slope["failures"]),
                "pycicy_models_checked": cohom["checked_models"],
                "pycicy_failure_count": cohom["failure_count"],
            },
        },
        {
            "id": "cicy2544_positive_favourable_outside_regime",
            "title": "Positive outside-regime favourable construction",
            "status": "verified_upstairs_construction",
            "claim": "CICY 2544 gives a finite h11=7 outside-old-regime segment with a clean upstairs one-Higgs SU(5) candidate.",
            "evidence": [
                "reports/outside_regime_higgs_candidate_certificate.json",
                "reports/outside_regime_higgs_deformation_line.json",
                "reports/outside_regime_higgs_candidate_independent_check.json",
                "reports/final_deliverable_verification.json",
            ],
            "key_numbers": {
                "cicy": cicy2544["construction"]["cicy"],
                "h11": cicy2544["construction"]["h11"],
                "spectrum_10_anti10_5bar_5": [
                    cicy2544["spectrum"]["upstairs_10"],
                    cicy2544["spectrum"]["upstairs_anti_10"],
                    cicy2544["spectrum"]["upstairs_5bar"],
                    cicy2544["spectrum"]["upstairs_5"],
                ],
                "h0_v": cicy2544["quality"]["h0_v"],
                "h0_v_dual": cicy2544["quality"]["h0_v_dual"],
                "trivial_summand_count": cicy2544["quality"][
                    "trivial_summand_count"
                ],
                "hard_gate_segment": deformation["family"][
                    "hard_gate_segment_in_checked_window"
                ],
                "one_higgs_n_values": deformation["family"]["one_higgs_n_values"],
                "index_v_polynomial_coefficients": deformation[
                    "polynomial_certificates"
                ]["index_v_coefficients"],
                "index_wedge2_polynomial_coefficients": deformation[
                    "polynomial_certificates"
                ]["index_wedge2_v_coefficients"],
            },
            "limitation": "No Wilson-line descent from current raw symmetry data because CICY2544 has no recorded free symmetry option.",
        },
        {
            "id": "favourable_quotient_no_go",
            "title": "Favourable quotient no-go audit",
            "status": "verified_no_go_at_geometry_selection",
            "claim": "The current cicylist.m has no favourable h11>=7 target that also has recorded free symmetry.",
            "evidence": [
                "reports/outside_regime_targets.json",
                "reports/outside_regime_free_symmetry_no_go.json",
                "reports/outside_regime_free_symmetry_no_go_verification.json",
            ],
            "key_numbers": {
                "canonical_h11_ge7_known_symmetry": favourable_no_go[
                    "target_pool_audit"
                ]["canonical_h11_ge_7_known_nonempty_symmetry_count"],
                "canonical_h11_ge7_recorded_free": favourable_no_go[
                    "target_pool_audit"
                ]["canonical_h11_ge_7_known_free_symmetry_count"],
                "favourable_h11_ge7_known_symmetry": favourable_no_go[
                    "target_pool_audit"
                ]["favourable_h11_ge_7_known_nonempty_symmetry_count"],
                "favourable_h11_ge7_recorded_free": favourable_no_go[
                    "target_pool_audit"
                ]["favourable_h11_ge_7_known_free_symmetry_count"],
                "favourable_known_symmetry_nums": favourable_no_go[
                    "target_pool_audit"
                ]["favourable_h11_ge_7_known_nonempty_symmetry_nums"],
            },
            "limitation": "This is a no-go for the favourable/free intersection in current raw data, not a theorem about all CICY presentations.",
        },
        {
            "id": "cicy7484_quotient_descent_near_miss",
            "title": "Quotient-compatible descent near-miss",
            "status": "verified_lift_compatible_near_miss",
            "claim": "CICY 7484 shows the quotient/Wilson-line character machinery is working, but vectorlike sectors are too large and the best point has a regularity caveat.",
            "evidence": [
                "reports/best_candidate_certificate.json",
                "reports/k_even_improved_family.json",
                "reports/candidate_equivariance_7484_shift12.json",
                "reports/candidate_novelty_7484_shift12.json",
            ],
            "key_numbers": {
                "cicy": cicy7484["construction"]["cicy"],
                "symmetry_order": cicy7484["construction"]["symmetry_order"],
                "upstairs_spectrum_10_anti10_5bar_5": [
                    cicy7484["spectrum"]["upstairs_10"],
                    cicy7484["spectrum"]["upstairs_anti_10"],
                    cicy7484["spectrum"]["upstairs_5bar"],
                    cicy7484["spectrum"]["upstairs_5"],
                ],
                "actual_per_character_pair_5bar_5": cicy7484["spectrum"][
                    "actual_per_character_pair"
                ],
                "trivial_summand_count": cicy7484["quality_caveat"][
                    "trivial_summand_count"
                ],
                "h0_v": cicy7484["quality_caveat"]["h0_v"],
                "h0_v_dual": cicy7484["quality_caveat"]["h0_v_dual"],
            },
            "limitation": "Not clean one-Higgs and not the non-favourable h11>=7 route.",
        },
        {
            "id": "cicy5259_nonfavourable_pilot_upgrade",
            "title": "Non-favourable pilot upgrade",
            "status": "partial_ambient_certification_layer_only",
            "claim": "CICY 5259 shows the non-favourable recorded-free pool is scoutable and has an ambient-restricted order-two breadcrumb, but full certification needs missing Picard-basis geometry and equivariant cohomology data.",
            "evidence": [
                "reports/nonfavourable_free_capability_audit.json",
                "reports/nonfavourable_ambient_restricted_scout.json",
                "reports/nonfavourable_extension_report.json",
                "reports/cicy5259_certifiability_upgrade_report.json",
                "reports/cicy5259_certifiability_upgrade_verification.json",
            ],
            "key_numbers": {
                "audited_recorded_free_nonfavourable_targets": nonfav[
                    "capability_audit_summary"
                ]["target_count"],
                "ambient_restricted_scoutable_targets": nonfav[
                    "capability_audit_summary"
                ]["ambient_restricted_scoutable_target_count"],
                "full_nonfavourable_certifiable_targets_now": nonfav[
                    "capability_audit_summary"
                ]["full_nonfavourable_certifiable_target_count"],
                "pilot_cicy": cicy5259["metadata"]["num"],
                "rank_defect": cicy5259["conclusion"][
                    "rank_defect_h11_minus_num_projective_factors"
                ],
                "pilot_spectrum_10_anti10_5bar_5": [
                    cicy5259["ambient_restricted_breadcrumb"]["spectrum"][
                        "upstairs_10"
                    ],
                    cicy5259["ambient_restricted_breadcrumb"]["spectrum"][
                        "upstairs_anti_10"
                    ],
                    cicy5259["ambient_restricted_breadcrumb"]["spectrum"][
                        "upstairs_5bar"
                    ],
                    cicy5259["ambient_restricted_breadcrumb"]["spectrum"][
                        "upstairs_5"
                    ],
                ],
                "pilot_index_v": cicy5259["ambient_restricted_breadcrumb"][
                    "index_v"
                ],
                "pilot_index_wedge2_v": cicy5259[
                    "ambient_restricted_breadcrumb"
                ]["index_wedge2_v"],
            },
            "limitation": cicy5259["conclusion"]["primary_blocker"],
        },
    ]

    artifact_table = [
        {
            "artifact": "reports/final_deliverable_verification.json",
            "role": "Top-level verification for benchmark reproduction and CICY2544 deliverable.",
            "status": "pass" if final["all_gates_pass"] else "fail",
        },
        {
            "artifact": "reports/outside_regime_higgs_candidate_certificate.json",
            "role": "CICY2544 one-Higgs upstairs candidate certificate.",
            "status": "pass" if all_pass(cicy2544["gate_checklist"]) else "fail",
        },
        {
            "artifact": "reports/outside_regime_higgs_deformation_line.json",
            "role": "CICY2544 finite deformation segment and polynomial certificates.",
            "status": "present",
        },
        {
            "artifact": "reports/outside_regime_free_symmetry_no_go.json",
            "role": "Favourable h11>=7 recorded-free target-pool no-go audit.",
            "status": "pass"
            if all_pass(favourable_no_go["gate_checklist"])
            else "fail",
        },
        {
            "artifact": "reports/best_candidate_certificate.json",
            "role": "CICY7484 quotient-compatible lift/character near-miss certificate.",
            "status": "pass" if all_pass(cicy7484["gate_checklist"]) else "fail",
        },
        {
            "artifact": "reports/nonfavourable_extension_report.json",
            "role": "Non-favourable recorded-free capability audit plus ambient scout summary.",
            "status": "pass" if all_pass(nonfav["gate_checklist"]) else "fail",
        },
        {
            "artifact": "reports/cicy5259_certifiability_upgrade_report.json",
            "role": "CICY5259 certifiability upgrade and trust-boundary report.",
            "status": "pass" if all_pass(cicy5259["gate_checklist"]) else "fail",
        },
    ]

    blocker_table = [
        {
            "route": "CICY2544 favourable upstairs candidate",
            "current_state": "clean upstairs one-Higgs SU(5) candidate",
            "blocker": "No recorded free symmetry option in current cicylist.m entry.",
            "next_input_needed": "A free action on this geometry/presentation, or move to a different quotient-compatible geometry.",
        },
        {
            "route": "favourable h11>=7 quotient-compatible search",
            "current_state": "geometry-selection no-go in current raw data",
            "blocker": "Favourable h11>=7 recorded-free target count is zero.",
            "next_input_needed": "New/free-symmetry data for a favourable h11>=7 presentation, or non-favourable machinery.",
        },
        {
            "route": "CICY7484 quotient-compatible descent",
            "current_state": "raw Z2xZ2 lift and character machinery work",
            "blocker": "Best verified point has vectorlike sectors (5bar,5)=(6,3) per character and two trivial summands.",
            "next_input_needed": "A cleaner regular/nontrivial lift-compatible construction or stronger search in this quotient-compatible sector.",
        },
        {
            "route": "CICY5259 non-favourable pilot",
            "current_state": "ambient-restricted breadcrumb with spectrum 6/0/16/10",
            "blocker": cicy5259["conclusion"]["primary_blocker"],
            "next_input_needed": "Full Picard basis, full h11 intersection tensor, full c2(TX), full Kahler/Mori cone, symmetry action on full Picard basis, full-Picard cohomology, and equivariant cohomology characters.",
        },
        {
            "route": "62-target non-favourable recorded-free pool",
            "current_state": "all 62 are ambient-restricted scoutable; zero full-certifiable now",
            "blocker": nonfav["conclusion"]["primary_blocker"],
            "next_input_needed": "A reusable non-favourable CICY geometry data source or algorithmic pipeline, piloted on CICY5259.",
        },
    ]

    next_inputs = [
        "For CICY5259, obtain or derive the missing seventh Picard-basis divisor and its intersection/c2/cone data.",
        "Build a full-Picard line-bundle cohomology bridge or a verified reduction from full charges to pyCICY-computable representatives.",
        "Compute the free Z2 action on the full Picard basis and the induced equivariant cohomology character decomposition.",
        "Only after those are in place, rerun the hard-gate search on CICY5259 and then expand to the other 61 recorded-free non-favourable targets.",
    ]

    return {
        "scope": "definite result stack for verifier-first heterotic line-bundle search",
        "status": "coherent_result_stack_ready_to_package",
        "headline": "The current state is a verified result stack: benchmark reproduction, a new clean upstairs CICY2544 outside-regime construction, a favourable quotient no-go in current cicylist data, a CICY7484 quotient-compatible near-miss, and a CICY5259 non-favourable pilot that localizes the missing geometry needed for true quotient-compatible search.",
        "verification_summary": verification_summary(),
        "result_stack": result_stack,
        "artifact_table": artifact_table,
        "blocker_table": blocker_table,
        "next_mathematical_inputs": next_inputs,
    }


def write_memo(package: dict[str, Any], path: Path) -> None:
    lines = [
        "# Definite Result Stack",
        "",
        package["headline"],
        "",
        "## Stack",
        "",
    ]
    for item in package["result_stack"]:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"Status: `{item['status']}`",
                "",
                item["claim"],
                "",
                f"Evidence: {', '.join(item['evidence'])}.",
                "",
            ]
        )
        if item.get("limitation"):
            lines.extend([f"Limitation: {item['limitation']}", ""])
    lines.extend(
        [
            "## Recommendation",
            "",
            "Pause broad search and present the stack as the current definite result. The next real mathematical input is non-favourable Picard-basis geometry, starting with CICY5259.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_artifact_table(package: dict[str, Any], path: Path) -> None:
    lines = [
        "# Result Stack Artifact Table",
        "",
        "| Artifact | Role | Status |",
        "|---|---|---|",
    ]
    for row in package["artifact_table"]:
        lines.append(f"| `{row['artifact']}` | {row['role']} | `{row['status']}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_blocker_table(package: dict[str, Any], path: Path) -> None:
    lines = [
        "# Result Stack Dependency And Blocker Table",
        "",
        "| Route | Current State | Blocker | Next Input Needed |",
        "|---|---|---|---|",
    ]
    for row in package["blocker_table"]:
        lines.append(
            f"| {row['route']} | {row['current_state']} | {row['blocker']} | {row['next_input_needed']} |"
        )
    lines.extend(["", "## Next Mathematical Inputs", ""])
    for item in package["next_mathematical_inputs"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "definite_result_stack_package.json"),
    )
    parser.add_argument(
        "--memo-out",
        default=str(REPORTS / "definite_result_stack_memo.md"),
    )
    parser.add_argument(
        "--artifact-table-out",
        default=str(REPORTS / "definite_result_stack_artifact_table.md"),
    )
    parser.add_argument(
        "--blocker-table-out",
        default=str(REPORTS / "definite_result_stack_dependency_blockers.md"),
    )
    args = parser.parse_args()

    package = build_package()
    json_out = Path(args.json_out)
    memo_out = Path(args.memo_out)
    artifact_out = Path(args.artifact_table_out)
    blocker_out = Path(args.blocker_table_out)

    json_out.write_text(json.dumps(package, indent=2, sort_keys=True), encoding="utf-8")
    write_memo(package, memo_out)
    write_artifact_table(package, artifact_out)
    write_blocker_table(package, blocker_out)

    print(f"status={package['status']}")
    print(
        "all_current_stack_verifiers_pass="
        f"{package['verification_summary']['all_current_stack_verifiers_pass']}"
    )
    print(f"json_out={json_out}")
    print(f"memo_out={memo_out}")
    print(f"artifact_table_out={artifact_out}")
    print(f"blocker_table_out={blocker_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
