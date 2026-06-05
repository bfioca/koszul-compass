#!/usr/bin/env python3
"""Build a certificate for the best outside-regime one-Higgs-pair candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_outside_regime_candidate_certificate import gate, novelty_context, write_markdown
from string_theory.novelty import novelty_record


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def is_one_higgs_candidate(record: dict[str, Any]) -> bool:
    spectrum = record["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    return (
        spectrum["upstairs_10"] == 3
        and spectrum["upstairs_anti_10"] == 0
        and spectrum["upstairs_5bar"] == 4
        and spectrum["upstairs_5"] == 1
    )


def candidate_score(record: dict[str, Any]) -> tuple:
    return (
        record["max_entry_abs"],
        record.get("delta_l1", 0),
        record["slope_search"]["max_normalized_slope"],
        sum(record["anomaly"]),
    )


def build_certificate() -> dict[str, Any]:
    report_name = "outside_regime_local_deformations_exact_chiral_delta1.json"
    local = load_json(report_name)
    target_pool = load_json("outside_regime_targets.json")
    candidates = [
        record
        for record in local["spectrum_pass_records"]
        if is_one_higgs_candidate(record)
    ]
    if not candidates:
        raise ValueError(f"no one-Higgs candidate found in reports/{report_name}")
    best = min(candidates, key=candidate_score)
    best = {**best, "cicy": local["search"]["cicy"]}
    target = next(
        item
        for item in target_pool["immediate_favourable_targets"]
        if item["num"] == best["cicy"]
    )
    spectrum = best["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    quality = best["cohomology_and_spectrum"]["line_bundle_sum_quality"]
    symmetry_order = abs(best["index_v"]) // 3
    novelty = {
        name: novelty_record(
            cicy_num=best["cicy"],
            symmetry_order=symmetry_order,
            matrix=best["matrix"],
            conf=target["conf"],
            dataset_keys=keys,
        )
        for name, keys in novelty_context()["key_sets"].items()
    }
    combined_novelty = novelty["combined"]
    construction = {
        "label": "outside_h11_7_cicy2544_local_exact_chiral_delta1_one_higgs_rank1",
        "cicy": best["cicy"],
        "h11": 7,
        "matrix": best["matrix"],
        "search_report": f"reports/{report_name}",
        "target_pool_report": "reports/outside_regime_targets.json",
        "outside_old_gutall_regime": True,
        "source": "local_deformation",
        "selection": "one_higgs_upstairs_su5",
        "base_candidate_label": local["base_context"]["base_candidate_label"],
        "base_search_report": local["base_context"]["base_candidate_search_report"],
        "base_candidate_certificate": local["base_context"][
            "base_candidate_certificate"
        ],
        "base_matrix": local["base_matrix"],
        "local_deformation_columns": best["columns"],
        "local_deformation_delta": best["delta"],
        "local_deformation_search": local["search"],
        "local_deformation_interpretation": local.get("interpretation"),
    }
    return {
        "scope": "best outside-GUTall favourable h11=7 upstairs SU(5) one-Higgs-pair candidate certified in current reports",
        "construction": construction,
        "gate_checklist": {
            "outside_regime_target": gate(
                best["cicy"]
                in target_pool["candidate_pool"]["immediate_favourable_target_nums"],
                "reports/outside_regime_targets.json",
                "CICY is a favourable h11=7 known-symmetry target outside GUTall h11<7 regime",
            ),
            "c1_zero": gate(
                best["c1"] == [0] * 7,
                construction["search_report"],
                f"c1(V)={best['c1']}",
            ),
            "index_chirality": gate(
                best["index_v"] == -3 and best["index_wedge2_v"] == -3,
                construction["search_report"],
                f"ind(V)={best['index_v']}, ind(wedge^2 V)={best['index_wedge2_v']}",
            ),
            "anomaly_effective": gate(
                all(value >= 0 for value in best["anomaly"]),
                construction["search_report"],
                f"ambient anomaly={best['anomaly']}",
            ),
            "slope_zero_numerical": gate(
                best["passes_slope_gate"],
                construction["search_report"],
                (
                    "max normalized slope="
                    f"{best['slope_search']['max_normalized_slope']:.3g}"
                ),
            ),
            "cohomology_spectrum": gate(
                best["passes_upstairs_spectrum_gate"]
                and spectrum["upstairs_anti_10"] == 0,
                construction["search_report"],
                (
                    f"upstairs 10/anti10/5bar/5="
                    f"{spectrum['upstairs_10']}/{spectrum['upstairs_anti_10']}/"
                    f"{spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}"
                ),
            ),
            "upstairs_one_higgs_pair": gate(
                spectrum["higgs_pair_candidates_upstairs"] == 1,
                construction["search_report"],
                "one vectorlike upstairs 5/5bar pair is present",
            ),
            "regular_nontrivial_quality": gate(
                quality["regular_nontrivial_summand_scan_style"],
                construction["search_report"],
                (
                    f"trivial_summands={quality['trivial_summand_count']}, "
                    f"h0(V)={quality['h0_v']}, h0(V*)={quality['h0_v_dual']}"
                ),
            ),
            "implemented_novelty": gate(
                combined_novelty["novel_under_row_and_column_permutation"],
                "data/raw/GUTall.m + data/raw/sms202.m",
                "novel against GUTall+sms202 under implemented row/column equivalences",
            ),
        },
        "spectrum": {
            "upstairs_10": spectrum["upstairs_10"],
            "upstairs_anti_10": spectrum["upstairs_anti_10"],
            "upstairs_5bar": spectrum["upstairs_5bar"],
            "upstairs_5": spectrum["upstairs_5"],
            "net_10_chirality": spectrum["net_10_chirality"],
            "net_5bar_chirality": spectrum["net_5bar_chirality"],
            "expected_upstairs_chirality": spectrum["expected_upstairs_chirality"],
            "higgs_pair_candidates_upstairs": spectrum[
                "higgs_pair_candidates_upstairs"
            ],
        },
        "quality": {
            "trivial_summand_count": quality["trivial_summand_count"],
            "h0_v": quality["h0_v"],
            "h0_v_dual": quality["h0_v_dual"],
            "regular_nontrivial_summand_scan_style": quality[
                "regular_nontrivial_summand_scan_style"
            ],
        },
        "novelty": novelty,
        "wilson_line_applicability": {
            "evidence": "reports/outside_regime_targets.json",
            "cicylist_symmetry_option_count": target["symmetry_option_count"],
            "raw_free_symmetry_option_count": target["free_symmetry_option_count"],
            "wilson_line_descent_applicable_from_recorded_raw_symmetry": target[
                "free_symmetry_option_count"
            ]
            > 0,
            "status": (
                "not_applicable_from_recorded_raw_cicylist_symmetry"
                if target["free_symmetry_option_count"] == 0
                else "requires_line_bundle_equivariance_and_cohomology_action_check"
            ),
            "interpretation": (
                "The raw cicylist.m entry has known symmetry data but no recorded "
                "free symmetry option, so this certificate treats the model as an "
                "upstairs SU(5) GUT candidate rather than a Wilson-line MSSM candidate."
            ),
        },
        "caveats": [
            "This is a deterministic sampled scout plus iterated local deformation hit, not an exhaustive outside-regime search.",
            "The slope-zero gate is numerical, not an exact poly-stability proof.",
            "The raw cicylist.m entry has known symmetry data but no recorded free symmetry option, so Wilson-line descent is not applicable from the recorded raw symmetry data.",
            "The candidate has an upstairs one-Higgs-pair SU(5) spectrum, but without Wilson-line descent it is not an exact MSSM spectrum.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_higgs_candidate_certificate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "outside_regime_higgs_candidate_certificate.md"),
    )
    args = parser.parse_args()

    certificate = build_certificate()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(certificate, md_out)
    print(f"label={certificate['construction']['label']}")
    print(f"cicy={certificate['construction']['cicy']}")
    print(
        "spectrum="
        f"{certificate['spectrum']['upstairs_10']}/"
        f"{certificate['spectrum']['upstairs_anti_10']}/"
        f"{certificate['spectrum']['upstairs_5bar']}/"
        f"{certificate['spectrum']['upstairs_5']}"
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
