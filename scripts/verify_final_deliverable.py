#!/usr/bin/env python3
"""Verify the final research deliverable package."""

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


def all_pass(mapping: dict[str, dict[str, Any]]) -> bool:
    return all(item["pass"] for item in mapping.values())


def verify() -> dict[str, Any]:
    dataset = load_json(REPORTS / "dataset_summary.json")
    gut_benchmark = load_json(REPORTS / "gut_benchmark_checks.json")
    slope_5000 = load_json(REPORTS / "gut_slope_checks_5000_adaptive.json")
    cohom_5000 = load_json(REPORTS / "gut_cohomology_smoke_5000_summary.json")
    targets = load_json(REPORTS / "outside_regime_targets.json")
    scout = load_json(REPORTS / "outside_regime_algebraic_scout_bound1_samples50000.json")
    exact_cert = load_json(REPORTS / "outside_regime_candidate_certificate.json")
    exact_check = load_json(REPORTS / "outside_regime_candidate_independent_check.json")
    higgs_cert = load_json(REPORTS / "outside_regime_higgs_candidate_certificate.json")
    higgs_check = load_json(REPORTS / "outside_regime_higgs_candidate_independent_check.json")
    deformation = load_json(REPORTS / "outside_regime_higgs_deformation_line.json")
    short_memo = (REPORTS / "short_research_memo.md").read_text(encoding="utf-8")
    notebook = load_json(ROOT / "notebooks" / "benchmark_verification.ipynb")

    benchmark_gates = {
        "raw_dataset_scale": gate(
            dataset["gutall"]["gut_model_count"] == 63325
            and dataset["sms202"]["model_count"] == 202,
            "reports/dataset_summary.json",
            "raw Oxford GUTall and sms202 dataset sizes match expected parsed counts",
        ),
        "old_scan_filter_recorded": gate(
            dataset["gutall"]["trivial_summand_count_distribution"] == {"0": 63325}
            and dataset["sms202"]["trivial_summand_count_distribution"] == {"0": 202},
            "reports/dataset_summary.json",
            "parsed old datasets have zero trivial summands in every model",
        ),
        "gut_algebraic_benchmark": gate(
            gut_benchmark["checked_models"] == 63325
            and not gut_benchmark["failures"],
            "reports/gut_benchmark_checks.json",
            "all known GUTall models pass algebraic benchmark gates",
        ),
        "slope_sample_benchmark": gate(
            slope_5000["checked_models"] == 5000
            and not slope_5000["failures"]
            and slope_5000["retry_count"] == slope_5000["retry_resolved_count"],
            "reports/gut_slope_checks_5000_adaptive.json",
            "first 5000 known models pass adaptive numerical slope gate",
        ),
        "cohomology_sample_benchmark": gate(
            cohom_5000["checked_models"] == 5000
            and cohom_5000["failure_count"] == 0
            and cohom_5000["all_euler_rr_and_upstairs_spectrum_checks_passed"],
            "reports/gut_cohomology_smoke_5000_summary.json",
            "first 5000 known models pass pyCICY cohomology/spectrum smoke gate",
        ),
    }

    outside_gates = {
        "outside_target_pool": gate(
            targets["candidate_pool"]["canonical_h11_ge_7_known_nonempty_symmetry_count"]
            == 108
            and targets["candidate_pool"][
                "favourable_h11_ge_7_known_nonempty_symmetry_count"
            ]
            == 3
            and targets["candidate_pool"]["immediate_favourable_target_nums"]
            == [2544, 3929, 4335],
            "reports/outside_regime_targets.json",
            "outside-old-regime h11>=7 known-symmetry pool and immediate favourable targets parsed",
        ),
        "scout_search": gate(
            scout["search"]["algebraic_survivor_count"] == 13482
            and scout["search"]["spectrum_pass_count"] == 9,
            "reports/outside_regime_algebraic_scout_bound1_samples50000.json",
            "sampled outside-regime scout found regular upstairs SU(5) candidates",
        ),
    }

    exact_spectrum = exact_cert["spectrum"]
    higgs_spectrum = higgs_cert["spectrum"]
    construction_gates = {
        "exact_chiral_certificate": gate(
            exact_cert["construction"]["label"]
            == "outside_h11_7_cicy2544_local_iterated_delta1_rank1"
            and all(item["pass"] for item in exact_cert["gate_checklist"].values())
            and exact_spectrum["upstairs_10"] == 3
            and exact_spectrum["upstairs_anti_10"] == 0
            and exact_spectrum["upstairs_5bar"] == 3
            and exact_spectrum["upstairs_5"] == 0,
            "reports/outside_regime_candidate_certificate.json",
            "exact-chiral upstairs SU(5) certificate passes all gates",
        ),
        "exact_chiral_independent_check": gate(
            exact_check["all_gates_pass"]
            and exact_check["construction"]["label"]
            == exact_cert["construction"]["label"],
            "reports/outside_regime_candidate_independent_check.json",
            "independent exact-chiral check passes",
        ),
        "one_higgs_certificate": gate(
            higgs_cert["construction"]["label"]
            == "outside_h11_7_cicy2544_local_exact_chiral_delta1_one_higgs_rank1"
            and all(item["pass"] for item in higgs_cert["gate_checklist"].values())
            and higgs_spectrum["upstairs_10"] == 3
            and higgs_spectrum["upstairs_anti_10"] == 0
            and higgs_spectrum["upstairs_5bar"] == 4
            and higgs_spectrum["upstairs_5"] == 1
            and higgs_spectrum["higgs_pair_candidates_upstairs"] == 1,
            "reports/outside_regime_higgs_candidate_certificate.json",
            "one-Higgs upstairs SU(5) certificate passes all gates",
        ),
        "one_higgs_independent_check": gate(
            higgs_check["all_gates_pass"]
            and higgs_check["construction"]["label"]
            == higgs_cert["construction"]["label"],
            "reports/outside_regime_higgs_candidate_independent_check.json",
            "independent one-Higgs check passes",
        ),
        "wilson_line_not_applicable": gate(
            not higgs_cert["wilson_line_applicability"][
                "wilson_line_descent_applicable_from_recorded_raw_symmetry"
            ]
            and higgs_cert["wilson_line_applicability"][
                "raw_free_symmetry_option_count"
            ]
            == 0,
            "reports/outside_regime_targets.json",
            "CICY 2544 has no recorded free symmetry option, so Wilson-line descent is not applicable from parsed raw data",
        ),
    }

    hard_segment = deformation["family"]["hard_gate_segment_in_checked_window"]
    segment_records = {
        record["n"]: record
        for record in deformation["records"]
        if record["passes_current_hard_gates"]
    }
    deformation_gates = {
        "finite_segment": gate(
            hard_segment == [0, 1, 2]
            and deformation["family"]["exact_chiral_n_values"] == [0]
            and deformation["family"]["one_higgs_n_values"] == [1],
            "reports/outside_regime_higgs_deformation_line.json",
            "finite deformation segment has exact-chiral n=0 and one-Higgs n=1",
        ),
        "exact_index_polynomials": gate(
            deformation["polynomial_certificates"]["index_v_coefficients"] == ["-3"]
            and deformation["polynomial_certificates"][
                "index_wedge2_v_coefficients"
            ]
            == ["-3"],
            "reports/outside_regime_higgs_deformation_line.json",
            "index and wedge2 index are exactly constant on the line",
        ),
        "segment_spectra": gate(
            segment_records[0]["cohomology_and_spectrum"]["su5_upstairs_spectrum"][
                "upstairs_5"
            ]
            == 0
            and segment_records[1]["cohomology_and_spectrum"][
                "su5_upstairs_spectrum"
            ]["upstairs_5"]
            == 1
            and segment_records[2]["cohomology_and_spectrum"][
                "su5_upstairs_spectrum"
            ]["upstairs_5"]
            == 6,
            "reports/outside_regime_higgs_deformation_line.json",
            "segment spectra are 3/0/3/0, 3/0/4/1, and 3/0/9/6",
        ),
    }

    notebook_source = "\n".join(
        "".join(cell.get("source", [])) for cell in notebook["cells"]
    )
    deliverable_gates = {
        "notebook_present": gate(
            "outside_regime_higgs_deformation_line.json" in notebook_source
            and "short_research_memo.md" in notebook_source,
            "notebooks/benchmark_verification.ipynb",
            "verification notebook asserts final construction and short memo artifacts",
        ),
        "short_memo_present": gate(
            "K(n) = K(0) + n D" in short_memo
            and "3/0/4/1" in short_memo
            and "Expert-Review Caveats" in short_memo,
            "reports/short_research_memo.md",
            "short research memo states construction, near-MSSM member, and caveats",
        ),
    }

    categories = {
        "benchmark_reproduction": benchmark_gates,
        "outside_regime_search": outside_gates,
        "candidate_certification": construction_gates,
        "deformation_segment": deformation_gates,
        "deliverables": deliverable_gates,
    }
    return {
        "scope": "final deliverable package verification for outside-regime CICY2544 construction",
        "categories": categories,
        "all_gates_pass": all(all_pass(gates) for gates in categories.values()),
        "summary": {
            "construction": "CICY2544 finite line-bundle segment K(n)=K(0)+nD",
            "hard_gate_segment": hard_segment,
            "near_mssm_member": "n=1 upstairs SU(5) spectrum 3/0/4/1",
            "wilson_line_status": "not_applicable_from_recorded_raw_cicylist_symmetry",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "final_deliverable_verification.json"),
    )
    args = parser.parse_args()

    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"all_gates_pass={result['all_gates_pass']}")
    print(f"json_out={out}")
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
