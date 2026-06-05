#!/usr/bin/env python3
"""Build a no-go/ranking report for favourable outside-regime free-symmetry targets."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RAW = ROOT / "data" / "raw"
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicylist import (  # noqa: E402
    extract_rule_value_text,
    parse_cicy_metadata,
    split_top_level_entries,
    split_top_level_list_items,
)


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def free_option_group_structures(entry: str, limit: int = 8) -> list[list[int]]:
    """Extract raw quotient group structures from free symmetry options.

    The raw CICY list stores each symmetry option as a Mathematica list whose
    first item is the freeness flag. In the options used by the current
    pipeline, the third top-level item records the quotient group structure.
    This deliberately stays lightweight: it is a raw diagnostic, not a full
    equivariant line-bundle lift computation.
    """

    if re.search(r'Symmetries\s*->\s*"unknown"', entry) or re.search(
        r"Symmetries\s*->\s*\{\}", entry
    ):
        return []
    structures: list[list[int]] = []
    for option_text in split_top_level_list_items(
        extract_rule_value_text(entry, "Symmetries")
    ):
        items = split_top_level_list_items(option_text)
        if not items or items[0].strip() != "True":
            continue
        structure = [int(value) for value in re.findall(r"-?\d+", items[2])]
        structures.append(structure)
        if len(structures) >= limit:
            break
    return structures


def compact_free_target(meta: dict[str, Any], entry: str) -> dict[str, Any]:
    return {
        "num": meta["Num"],
        "h11": meta["H11"],
        "h21": meta["H21"],
        "num_projective_factors": meta["NumPs"],
        "favourable_by_h11_equals_num_projective_factors": meta["H11"]
        == meta["NumPs"],
        "symmetry_option_count": meta["SymmetryOptionCount"],
        "free_symmetry_option_count": meta["FreeSymmetryOptionCount"],
        "sample_free_quotient_group_structures": free_option_group_structures(entry),
        "first_failing_gate_for_current_goal": (
            "nonfavourable_geometry_for_current_ambient_basis_verifier"
            if meta["H11"] != meta["NumPs"]
            else "none"
        ),
    }


def best_scout_spectra_by_target(scout: dict[str, Any]) -> dict[int, dict[str, Any]]:
    by_target: dict[int, dict[str, Any]] = {}
    for target_report in scout["target_reports"]:
        spectra = []
        for record in target_report["slope_checked_records"]:
            if not record.get("passes_upstairs_spectrum_gate"):
                continue
            spectrum = record["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
            quality = record["cohomology_and_spectrum"]["line_bundle_sum_quality"]
            spectra.append(
                {
                    "matrix": record["matrix"],
                    "index_v": record["index_v"],
                    "index_wedge2_v": record["index_wedge2_v"],
                    "anomaly": record["anomaly"],
                    "max_normalized_slope": record["slope_search"][
                        "max_normalized_slope"
                    ],
                    "spectrum": {
                        "upstairs_10": spectrum["upstairs_10"],
                        "upstairs_anti_10": spectrum["upstairs_anti_10"],
                        "upstairs_5bar": spectrum["upstairs_5bar"],
                        "upstairs_5": spectrum["upstairs_5"],
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
                }
            )
        spectra.sort(
            key=lambda item: (
                item["spectrum"]["upstairs_anti_10"],
                item["spectrum"]["higgs_pair_candidates_upstairs"],
                item["max_normalized_slope"],
            )
        )
        by_target[target_report["target"]["num"]] = {
            "sample_count": target_report["sample_count"],
            "unique_matrix_count": target_report["unique_matrix_count"],
            "algebraic_survivor_count": target_report["algebraic_survivor_count"],
            "slope_checked_count": target_report["slope_checked_count"],
            "slope_feasible_count": target_report["slope_feasible_count"],
            "spectrum_pass_count": target_report["spectrum_pass_count"],
            "best_sampled_spectrum_records": spectra[:3],
        }
    return by_target


def geometry_gate_table(
    targets: dict[str, Any],
    scout: dict[str, Any],
    higgs_cert: dict[str, Any],
) -> list[dict[str, Any]]:
    scout_by_target = best_scout_spectra_by_target(scout)
    table: list[dict[str, Any]] = []
    for target in targets["immediate_favourable_targets"]:
        num = target["num"]
        is_2544_higgs = num == higgs_cert["construction"]["cicy"]
        table.append(
            {
                "num": num,
                "h11": target["h11"],
                "h21": target["h21"],
                "num_projective_factors": target["num_projective_factors"],
                "favourable": target[
                    "favourable_by_h11_equals_num_projective_factors"
                ],
                "symmetry_option_count": target["symmetry_option_count"],
                "free_symmetry_option_count": target["free_symmetry_option_count"],
                "first_failing_gate_for_quotient_compatible_goal": (
                    "free_symmetry_required_for_wilson_line_descent"
                    if target["free_symmetry_option_count"] == 0
                    else "requires_line_bundle_lift_diagnostic"
                ),
                "sampled_scout": scout_by_target.get(num),
                "best_known_template_application": (
                    {
                        "source": "reports/outside_regime_higgs_candidate_certificate.json",
                        "status": "clean_upstairs_one_higgs_pair_but_no_recorded_free_symmetry",
                        "spectrum": higgs_cert["spectrum"],
                        "quality": higgs_cert["quality"],
                        "gate_checklist": higgs_cert["gate_checklist"],
                    }
                    if is_2544_higgs
                    else {
                        "source": "reports/outside_regime_algebraic_scout_bound1_samples50000.json",
                        "status": "sampled_scout_found_no_clean_one_higgs_template_member",
                    }
                ),
            }
        )
    return table


def comparison_summary(
    higgs_cert: dict[str, Any], deformation: dict[str, Any], best_7484: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "label": higgs_cert["construction"]["label"],
            "geometry": "CICY 2544",
            "reason": "cleanest upstairs one-Higgs construction in current reports",
            "quotient_compatible": False,
            "blocking_gate": "raw_free_symmetry_option_count=0",
            "spectrum": higgs_cert["spectrum"],
            "quality": higgs_cert["quality"],
            "polynomial_certificates": deformation["polynomial_certificates"],
            "hard_gate_segment": deformation["family"][
                "hard_gate_segment_in_checked_window"
            ],
        },
        {
            "rank": 2,
            "label": best_7484["construction"]["label"],
            "geometry": "CICY 7484",
            "reason": "best current lift-compatible character-certified comparison point",
            "quotient_compatible": True,
            "blocking_gate": "not_favourable_outside_regime_target_for_this_search_and_not_clean_one_higgs",
            "spectrum": best_7484["spectrum"],
            "quality": best_7484["quality_caveat"],
            "polynomial_certificates": best_7484["construction"][
                "polynomial_certificates"
            ],
        },
    ]


def build_report() -> dict[str, Any]:
    targets = load_json("outside_regime_targets.json")
    scout = load_json("outside_regime_algebraic_scout_bound1_samples50000.json")
    higgs_cert = load_json("outside_regime_higgs_candidate_certificate.json")
    deformation = load_json("outside_regime_higgs_deformation_line.json")
    best_7484 = load_json("best_candidate_certificate.json")

    entries = split_top_level_entries((RAW / "cicylist.m").read_text(encoding="utf-8"))
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    paired = list(zip(metadata, entries))
    h11_known = [
        (meta, entry)
        for meta, entry in paired
        if meta["Num"] <= 7890
        and meta["H11"] >= 7
        and meta["HasKnownNonemptySymmetryData"]
    ]
    h11_free = [
        (meta, entry)
        for meta, entry in h11_known
        if meta["FreeSymmetryOptionCount"] > 0
    ]
    favourable_known = [
        (meta, entry) for meta, entry in h11_known if meta["H11"] == meta["NumPs"]
    ]
    favourable_free = [
        (meta, entry)
        for meta, entry in favourable_known
        if meta["FreeSymmetryOptionCount"] > 0
    ]

    h11_free_counts = Counter(meta["H11"] for meta, _ in h11_free)
    nonfav_free_targets = [
        compact_free_target(meta, entry)
        for meta, entry in h11_free
        if meta["H11"] != meta["NumPs"]
    ]

    gates = {
        "favourable_known_symmetry_pool_identified": gate(
            len(favourable_known) == 3
            and [meta["Num"] for meta, _ in favourable_known] == [2544, 3929, 4335],
            "reports/outside_regime_targets.json",
            "current favourable h11>=7 known-symmetry ambient-basis pool is CICY 2544/3929/4335",
        ),
        "free_symmetry_pool_nonempty": gate(
            len(h11_free) == 62,
            "data/raw/cicylist.m",
            "canonical h11>=7 raw CICY list has recorded free-symmetry options",
        ),
        "favourable_free_intersection_empty": gate(
            len(favourable_free) == 0,
            "data/raw/cicylist.m + reports/outside_regime_targets.json",
            "no canonical h11>=7 target is both favourable and recorded-free in current metadata",
        ),
        "cicy2544_positive_template_verified_upstairs": gate(
            all(item["pass"] for item in higgs_cert["gate_checklist"].values())
            and higgs_cert["spectrum"]["upstairs_10"] == 3
            and higgs_cert["spectrum"]["upstairs_anti_10"] == 0
            and higgs_cert["spectrum"]["upstairs_5bar"] == 4
            and higgs_cert["spectrum"]["upstairs_5"] == 1,
            "reports/outside_regime_higgs_candidate_certificate.json",
            "CICY 2544 template remains clean upstairs one-Higgs but lacks recorded free symmetry",
        ),
        "cicy7484_comparison_loaded": gate(
            best_7484["gate_checklist"]["raw_z2xz2_lift"]["pass"]
            and best_7484["spectrum"]["actual_per_character_pair"] == [6, 3],
            "reports/best_candidate_certificate.json",
            "CICY 7484 comparison is lift-compatible but not clean one-Higgs",
        ),
    }

    return {
        "scope": "no-go audit for CICY2544-style clean upstairs line-bundle constructions on favourable outside-regime CICYs with recorded free symmetries",
        "conclusion": {
            "status": "no_quotient_compatible_favourable_target_in_current_cicylist",
            "short_reason": "The requested favourable h11>=7 known-free-symmetry target pool is empty in data/raw/cicylist.m.",
            "construction_found": False,
            "no_go_is_at_geometry_selection_gate": True,
            "next_mathematical_route": "Implement non-favourable CICY line-bundle verification or import a favourable-basis/free-symmetry dataset before Wilson-line descent can be pursued for the 62 recorded-free h11>=7 targets.",
        },
        "gate_checklist": gates,
        "target_pool_audit": {
            "canonical_h11_ge_7_known_nonempty_symmetry_count": len(h11_known),
            "canonical_h11_ge_7_known_free_symmetry_count": len(h11_free),
            "canonical_h11_ge_7_known_free_symmetry_h11_counts": dict(
                sorted(h11_free_counts.items())
            ),
            "favourable_h11_ge_7_known_nonempty_symmetry_count": len(
                favourable_known
            ),
            "favourable_h11_ge_7_known_nonempty_symmetry_nums": [
                meta["Num"] for meta, _ in favourable_known
            ],
            "favourable_h11_ge_7_known_free_symmetry_count": len(favourable_free),
            "favourable_h11_ge_7_known_free_symmetry_nums": [
                meta["Num"] for meta, _ in favourable_free
            ],
        },
        "favourable_geometry_gate_table": geometry_gate_table(
            targets, scout, higgs_cert
        ),
        "nonfavourable_recorded_free_symmetry_targets": nonfav_free_targets,
        "ranked_comparison": comparison_summary(higgs_cert, deformation, best_7484),
        "raw_symmetry_lift_diagnostic_policy": {
            "favourable_targets": "raw cicylist symmetry options have no free-action option, so Wilson-line descent is not applicable from recorded data",
            "nonfavourable_free_targets": "raw free-action options exist, but H11 != NumPs; current ambient-basis index/anomaly/slope/cohomology verifier is not a certificate for the full Picard basis",
            "lift_status": "no line-bundle equivariant lift attempted for the 62 non-favourable free targets in this report",
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Outside-Regime Free-Symmetry No-Go Audit",
        "",
        f"Status: `{report['conclusion']['status']}`",
        "",
        report["conclusion"]["short_reason"],
        "",
        "## Target Pool",
        "",
    ]
    pool = report["target_pool_audit"]
    lines.extend(
        [
            f"- canonical h11>=7 known-symmetry targets: {pool['canonical_h11_ge_7_known_nonempty_symmetry_count']}",
            f"- canonical h11>=7 recorded-free targets: {pool['canonical_h11_ge_7_known_free_symmetry_count']}",
            f"- favourable h11>=7 known-symmetry targets: {pool['favourable_h11_ge_7_known_nonempty_symmetry_nums']}",
            f"- favourable h11>=7 recorded-free targets: {pool['favourable_h11_ge_7_known_free_symmetry_nums']}",
            "",
            "## Favourable Geometry Gates",
            "",
            "| CICY | h11 | H11=NumPs | sym opts | free opts | first failing gate |",
            "|---:|---:|:---:|---:|---:|---|",
        ]
    )
    for row in report["favourable_geometry_gate_table"]:
        lines.append(
            "| {num} | {h11} | {fav} | {sym} | {free} | `{gate}` |".format(
                num=row["num"],
                h11=row["h11"],
                fav="yes" if row["favourable"] else "no",
                sym=row["symmetry_option_count"],
                free=row["free_symmetry_option_count"],
                gate=row["first_failing_gate_for_quotient_compatible_goal"],
            )
        )
    lines.extend(["", "## Ranked Comparison", ""])
    for item in report["ranked_comparison"]:
        lines.extend(
            [
                f"{item['rank']}. **{item['geometry']}** `{item['label']}`",
                f"   - reason: {item['reason']}",
                f"   - quotient compatible: {item['quotient_compatible']}",
                f"   - blocking gate: `{item['blocking_gate']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Next Route",
            "",
            report["conclusion"]["next_mathematical_route"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_free_symmetry_no_go.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "outside_regime_free_symmetry_no_go.md"),
    )
    args = parser.parse_args()

    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['conclusion']['status']}")
    print(
        "favourable_free_count="
        f"{report['target_pool_audit']['favourable_h11_ge_7_known_free_symmetry_count']}"
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
