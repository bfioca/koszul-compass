#!/usr/bin/env python3
"""Build final report for the non-favourable recorded-free extension attempt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def ambient_hit_summary(record: dict[str, Any]) -> dict[str, Any]:
    spectrum = record["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    quality = record["cohomology_and_spectrum"]["line_bundle_sum_quality"]
    return {
        "status": "ambient_restricted_breadcrumb_not_full_certificate",
        "cicy": record["cicy"],
        "matrix": record["matrix"],
        "ambient_restricted_index_v": record["ambient_restricted_index_v"],
        "ambient_restricted_index_wedge2_v": record[
            "ambient_restricted_index_wedge2_v"
        ],
        "expected_index_from_min_free_order": record[
            "expected_index_from_min_free_order"
        ],
        "anomaly": record["anomaly"],
        "compatible_free_options": record["compatible_free_options"],
        "slope_zero_evidence": {
            "max_normalized_slope": record["slope_search"][
                "max_normalized_slope"
            ],
            "kahler_point": record["slope_search"]["kahler_point"],
            "scope": "ambient positive orthant approximation only",
        },
        "spectrum": {
            "upstairs_10": spectrum["upstairs_10"],
            "upstairs_anti_10": spectrum["upstairs_anti_10"],
            "upstairs_5bar": spectrum["upstairs_5bar"],
            "upstairs_5": spectrum["upstairs_5"],
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
        "novelty": record["novelty"],
        "blocking_missing_data": [
            "full h11 divisor/Picard basis",
            "full h11 triple-intersection form",
            "full h11 c2(TX)",
            "full non-favourable Kahler/Mori cone",
            "line-bundle cohomology for arbitrary full-Picard charge vectors",
            "actual cohomology representation and Wilson-line character decomposition",
        ],
    }


def build_report() -> dict[str, Any]:
    audit = load_json("nonfavourable_free_capability_audit.json")
    scout = load_json("nonfavourable_ambient_restricted_scout.json")
    cicy2544 = load_json("outside_regime_higgs_candidate_certificate.json")
    cicy7484 = load_json("best_candidate_certificate.json")

    ambient_hits = [ambient_hit_summary(record) for record in scout["best_spectrum_records"]]
    best_hit = ambient_hits[0] if ambient_hits else None
    gates = {
        "capability_audit_complete_for_62_targets": gate(
            audit["conclusion"]["target_count"] == 62
            and len(audit["targets"]) == 62,
            "reports/nonfavourable_free_capability_audit.json",
            "all canonical h11>=7 recorded-free non-favourable targets are audited",
        ),
        "full_extension_blocker_identified": gate(
            audit["conclusion"]["full_nonfavourable_certifiable_target_count"] == 0
            and audit["conclusion"]["status"]
            == "full_nonfavourable_extension_blocked_by_missing_full_geometry_data",
            "reports/nonfavourable_free_capability_audit.json",
            "current workspace lacks full non-favourable Picard/intersection/c2/cone data",
        ),
        "ambient_restricted_scout_attempted": gate(
            scout["search"]["target_nums"] == [4185, 5259, 4078]
            and scout["search"]["samples_per_target"] == 10000
            and scout["search"]["algebraic_survivor_count"] > 0,
            "reports/nonfavourable_ambient_restricted_scout.json",
            "small scout ran on top rank-defect-one recorded-free targets",
        ),
        "ambient_restricted_hit_recorded": gate(
            bool(best_hit)
            and best_hit["cicy"] == 5259
            and best_hit["ambient_restricted_index_v"] == -6
            and best_hit["ambient_restricted_index_wedge2_v"] == -6
            and best_hit["spectrum"]["upstairs_10"] == 6
            and best_hit["spectrum"]["upstairs_anti_10"] == 0,
            "reports/nonfavourable_ambient_restricted_scout.json",
            "CICY5259 ambient-restricted breadcrumb passes sampled upstairs gates",
        ),
        "anchors_loaded": gate(
            cicy2544["spectrum"]["upstairs_10"] == 3
            and cicy2544["spectrum"]["upstairs_5"] == 1
            and cicy7484["gate_checklist"]["raw_z2xz2_lift"]["pass"],
            "reports/outside_regime_higgs_candidate_certificate.json + reports/best_candidate_certificate.json",
            "CICY2544 and CICY7484 anchor evidence loaded for ranking",
        ),
    }
    return {
        "scope": "non-favourable h11>=7 recorded-free line-bundle verifier extension report",
        "conclusion": {
            "status": "no_full_nonfavourable_quotient_candidate_yet",
            "candidate_found": False,
            "ambient_restricted_breadcrumb_found": bool(best_hit),
            "primary_blocker": audit["conclusion"]["primary_blocker"],
            "next_required_data_or_capability": [
                "import or derive full Picard-basis divisor data for non-favourable CICYs",
                "compute full h11 intersection tensors and c2(TX) in that basis",
                "construct a reliable full Kahler/Mori cone approximation",
                "extend pyCICY/cohomology interface beyond ambient-restricted charges or map full charges to computable representatives",
                "compute actual equivariant cohomology representations for Wilson-line projection",
            ],
        },
        "gate_checklist": gates,
        "capability_audit_summary": {
            "target_count": audit["conclusion"]["target_count"],
            "ambient_restricted_scoutable_target_count": audit["conclusion"][
                "ambient_restricted_scoutable_target_count"
            ],
            "full_nonfavourable_certifiable_target_count": audit["conclusion"][
                "full_nonfavourable_certifiable_target_count"
            ],
            "rank_defect_counts": audit["summary"]["rank_defect_counts"],
            "top_tractable_target_nums": audit["summary"]["top_tractable_target_nums"],
        },
        "ambient_restricted_scout_summary": scout["search"],
        "ambient_restricted_hits": ambient_hits,
        "ranked_comparison": [
            {
                "rank": 1,
                "label": "CICY5259 ambient-restricted scout hit",
                "geometry": "CICY 5259",
                "role": "first non-favourable recorded-free breadcrumb",
                "full_quotient_certificate": False,
                "reason": "passes sampled ambient-restricted gates and raw row-trivial free-option compatibility, but lacks full non-favourable geometry data",
                "spectrum": best_hit["spectrum"] if best_hit else None,
                "blocking_gate": "missing_full_nonfavourable_picard_intersection_c2_cone_and_character_data",
            },
            {
                "rank": 2,
                "label": cicy2544["construction"]["label"],
                "geometry": "CICY 2544",
                "role": "clean upstairs one-Higgs anchor",
                "full_quotient_certificate": False,
                "reason": "clean upstairs 3/0/4/1 spectrum, regular/nontrivial, but no recorded free symmetry",
                "spectrum": cicy2544["spectrum"],
                "blocking_gate": "raw_free_symmetry_option_count=0",
            },
            {
                "rank": 3,
                "label": cicy7484["construction"]["label"],
                "geometry": "CICY 7484",
                "role": "quotient-compatible character-certified anchor",
                "full_quotient_certificate": True,
                "reason": "raw Z2xZ2 lift exists, but current best has trivial-summand caveat and not clean one-Higgs",
                "spectrum": cicy7484["spectrum"],
                "blocking_gate": "not_clean_one_higgs_and_not_nonfavourable_h11_ge7_target",
            },
        ],
        "interpretation": {
            "ambient_restricted_search_value": "The scout shows the selected non-favourable free targets have ambient-restricted line-bundle matrices satisfying the cheap hard gates, so a real extension may be worth pursuing once full geometry data is available.",
            "why_not_complete_candidate": "For non-favourable CICYs H11 > NumPs, ambient checks do not cover line bundles in the missing Picard directions and do not certify the full anomaly, slope chamber, or Wilson-line spectrum.",
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Non-Favourable Extension Report",
        "",
        f"Status: `{report['conclusion']['status']}`",
        "",
        report["conclusion"]["primary_blocker"],
        "",
        "## Capability Audit",
        "",
    ]
    summary = report["capability_audit_summary"]
    lines.extend(
        [
            f"- targets audited: {summary['target_count']}",
            f"- ambient-restricted scoutable: {summary['ambient_restricted_scoutable_target_count']}",
            f"- full non-favourable certifiable now: {summary['full_nonfavourable_certifiable_target_count']}",
            f"- top tractable target nums: {summary['top_tractable_target_nums'][:10]}",
            "",
            "## Ambient-Restricted Scout",
            "",
        ]
    )
    scout = report["ambient_restricted_scout_summary"]
    lines.extend(
        [
            f"- targets: {scout['target_nums']}",
            f"- samples per target: {scout['samples_per_target']}",
            f"- algebraic survivors: {scout['algebraic_survivor_count']}",
            f"- slope feasible: {scout['slope_feasible_count']}",
            f"- spectrum pass: {scout['spectrum_pass_count']}",
            "",
            "## Ranked Comparison",
            "",
        ]
    )
    for item in report["ranked_comparison"]:
        lines.extend(
            [
                f"{item['rank']}. **{item['geometry']}** `{item['label']}`",
                f"   - role: {item['role']}",
                f"   - full quotient certificate: {item['full_quotient_certificate']}",
                f"   - blocking gate: `{item['blocking_gate']}`",
            ]
        )
    lines.extend(["", "## Interpretation", "", report["interpretation"]["why_not_complete_candidate"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "nonfavourable_extension_report.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "nonfavourable_extension_report.md"),
    )
    args = parser.parse_args()

    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['conclusion']['status']}")
    print(f"ambient_restricted_breadcrumb_found={report['conclusion']['ambient_restricted_breadcrumb_found']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
