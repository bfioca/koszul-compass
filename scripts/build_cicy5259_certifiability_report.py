#!/usr/bin/env python3
"""Build a certifiability upgrade report for non-favourable CICY 5259."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import (  # noqa: E402
    ambient_dimensions,
    bundle_c1,
    triple_intersections,
)
from string_theory.cicylist import (  # noqa: E402
    parse_cicy_metadata,
    parse_integer_list_rule,
    split_top_level_entries,
)


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def cicy5259_raw() -> tuple[dict[str, Any], str, list[list[int]], list[int]]:
    entries = split_top_level_entries((RAW / "cicylist.m").read_text(encoding="utf-8"))
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    for meta, entry in zip(metadata, entries):
        if meta["Num"] == 5259:
            return meta, entry, parse_integer_list_rule(entry, "Conf"), parse_integer_list_rule(entry, "C2")
    raise ValueError("CICY 5259 not found")


def intersection_summary(conf: list[list[int]]) -> dict[str, Any]:
    d = triple_intersections(conf)
    nonzero = {
        key: value for key, value in d.items() if value != 0
    }
    return {
        "ambient_tensor_rank": len(conf),
        "nonzero_count": len(nonzero),
        "max_abs_value": max((abs(value) for value in nonzero.values()), default=0),
        "sha256": sha256(
            json.dumps(
                [[list(key), value] for key, value in sorted(nonzero.items())],
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
        "sample_nonzero": [
            {"indices": list(key), "value": value}
            for key, value in sorted(nonzero.items())[:24]
        ],
    }


def pycicy_probe(conf: list[list[int]], c2: list[int]) -> dict[str, Any]:
    try:
        from string_theory.cohomology import line_cohomology, make_pycicy, pycicy_config

        cy = make_pycicy(pycicy_config(conf))
        hodge_data = [float(value) for value in cy.hodge_data()]
        second_chern = [int(round(float(value))) for value in cy.second_chern()]
        triple = cy.triple_intersection()
        if hasattr(triple, "tolist"):
            triple = triple.tolist()
        helper = triple_intersections(conf)
        triple_agrees = True
        for i in range(len(conf)):
            for j in range(len(conf)):
                for k in range(len(conf)):
                    if int(round(float(triple[i][j][k]))) != helper[(i, j, k)]:
                        triple_agrees = False
        zero_cohomology = line_cohomology(conf, [0] * len(conf))
        line_index_formula = str(cy.line_index())
        line_slope_formula = str(cy.line_slope())
        return {
            "available": True,
            "hodge_data_raw": hodge_data,
            "h11_matches_metadata": round(hodge_data[2]) == 7,
            "h21_matches_metadata": round(hodge_data[1]) == 31,
            "second_chern": second_chern,
            "second_chern_matches_raw_ambient_c2": second_chern == c2,
            "ambient_triple_intersection_matches_helper": triple_agrees,
            "zero_bundle_cohomology": zero_cohomology,
            "zero_bundle_matches_calabi_yau_expectation": zero_cohomology
            == [1, 0, 0, 1],
            "line_index_formula_scope": "ambient-restricted charge variables m0..m5",
            "line_index_formula": line_index_formula,
            "line_slope_formula_scope": "ambient-restricted charge variables m0..m5 and ambient Kahler variables t0..t5",
            "line_slope_formula": line_slope_formula,
        }
    except Exception as exc:  # pragma: no cover - environment diagnostic
        return {
            "available": False,
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
        }


def same_hodge_local_inventory() -> dict[str, Any]:
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    same = [
        meta
        for meta in metadata
        if meta["Num"] <= 7890 and meta["H11"] == 7 and meta["H21"] == 31
    ]
    favourable = [meta for meta in same if meta["H11"] == meta["NumPs"]]
    recorded_free = [meta for meta in same if meta["FreeSymmetryOptionCount"] > 0]
    return {
        "same_hodge_count": len(same),
        "same_hodge_favourable_count": len(favourable),
        "same_hodge_recorded_free_count": len(recorded_free),
        "sample_favourable_nums": [meta["Num"] for meta in favourable[:24]],
        "recorded_free_nums": [meta["Num"] for meta in recorded_free],
        "import_status": "not_importable_as_5259_full_basis_without_explicit_isomorphism_or_divisor_map",
    }


def build_report() -> dict[str, Any]:
    meta, _entry, conf, c2 = cicy5259_raw()
    audit = load_json("nonfavourable_free_capability_audit.json")
    extension = load_json("nonfavourable_extension_report.json")
    scout = load_json("nonfavourable_ambient_restricted_scout.json")
    target_audit = next(item for item in audit["targets"] if item["num"] == 5259)
    hit = next(record for record in scout["best_spectrum_records"] if record["cicy"] == 5259)
    pycicy = pycicy_probe(conf, c2)
    ambient_summary = intersection_summary(conf)
    dims = list(ambient_dimensions(conf))
    rank_defect = meta["H11"] - meta["NumPs"]
    c1_zero = bundle_c1(hit["matrix"]) == [0] * meta["NumPs"]
    hit_spectrum = hit["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    hit_quality = hit["cohomology_and_spectrum"]["line_bundle_sum_quality"]

    quantities = {
        "configuration_matrix": {
            "status": "available_exact_from_cicylist",
            "value": conf,
            "trust": "full defining complete-intersection configuration",
        },
        "ambient_dimensions": {
            "status": "derived_exact_from_configuration",
            "value": dims,
            "trust": "full ambient product data",
        },
        "hodge_numbers": {
            "status": "available_from_cicylist_and_pycicy",
            "h11": meta["H11"],
            "h21": meta["H21"],
            "trust": "full topological Hodge numbers",
        },
        "ambient_divisor_basis": {
            "status": "available",
            "rank": meta["NumPs"],
            "trust": "ambient-restricted Picard sublattice only",
        },
        "full_picard_divisor_basis": {
            "status": "missing",
            "rank": meta["H11"],
            "missing_rank": rank_defect,
            "trust": "required for full non-favourable line-bundle certification",
        },
        "ambient_intersection_tensor": {
            "status": "derived_exact_from_configuration_and_cross_checked_with_pycicy",
            "summary": ambient_summary,
            "trust": "ambient-restricted triple intersections only",
        },
        "full_h11_intersection_tensor": {
            "status": "missing",
            "rank": meta["H11"],
            "trust": "required for full index, anomaly, and slope certificates",
        },
        "ambient_c2_tx": {
            "status": "available_from_cicylist_and_pycicy",
            "value": c2,
            "trust": "ambient-restricted c2 components only",
        },
        "full_h11_c2_tx": {
            "status": "missing",
            "rank": meta["H11"],
            "trust": "required for full anomaly and index certificates",
        },
        "ambient_kahler_cone_approximation": {
            "status": "available_positive_orthant",
            "trust": "suggestive slope chamber only; not full non-favourable Kahler cone",
        },
        "full_kahler_mori_cone": {
            "status": "missing",
            "trust": "required for full slope-zero and anomaly-effectiveness certification",
        },
        "raw_free_coordinate_symmetry": {
            "status": "available_from_cicylist",
            "free_option_count": meta["FreeSymmetryOptionCount"],
            "trust": "raw coordinate action data for recorded free Z2 options",
        },
        "symmetry_action_on_ambient_divisors": {
            "status": "derived_for_recorded_options",
            "free_options_with_ambient_row_permutation_inference": target_audit[
                "symmetry_action"
            ]["free_options_with_ambient_row_permutation_inference"],
            "trust": "ambient divisor row action only",
        },
        "symmetry_action_on_full_picard_basis": {
            "status": "missing",
            "trust": "required for full line-bundle invariance/equivariant lift",
        },
        "ambient_line_bundle_cohomology": {
            "status": "available_via_pycicy",
            "trust": "ambient-restricted line bundles only",
        },
        "full_picard_line_bundle_cohomology": {
            "status": "missing",
            "trust": "required for arbitrary full-Picard line bundles and complete search",
        },
        "equivariant_cohomology_characters": {
            "status": "missing",
            "trust": "required for Wilson-line spectrum projection",
        },
    }
    gates = {
        "raw_5259_metadata_loaded": gate(
            meta["Num"] == 5259
            and meta["H11"] == 7
            and meta["NumPs"] == 6
            and meta["FreeSymmetryOptionCount"] == 8,
            "data/raw/cicylist.m",
            "CICY5259 is non-favourable with rank defect one and eight free options",
        ),
        "pycicy_ambient_cross_check": gate(
            pycicy.get("available")
            and pycicy.get("second_chern_matches_raw_ambient_c2")
            and pycicy.get("ambient_triple_intersection_matches_helper")
            and pycicy.get("zero_bundle_matches_calabi_yau_expectation"),
            "pyCICY + src/string_theory/cicy.py",
            "ambient C2, triple intersections, and zero-bundle cohomology cross-check",
        ),
        "breadcrumb_ambient_gates_loaded": gate(
            c1_zero
            and hit["ambient_restricted_index_v"] == -6
            and hit["ambient_restricted_index_wedge2_v"] == -6
            and all(value >= 0 for value in hit["anomaly"])
            and hit["passes_ambient_restricted_slope_gate"]
            and hit["passes_upstairs_spectrum_gate"]
            and hit_quality["regular_nontrivial_summand_scan_style"],
            "reports/nonfavourable_ambient_restricted_scout.json",
            "CICY5259 breadcrumb passes ambient-restricted hard gates",
        ),
        "full_certification_blocker_explicit": gate(
            quantities["full_picard_divisor_basis"]["status"] == "missing"
            and quantities["full_h11_intersection_tensor"]["status"] == "missing"
            and quantities["full_h11_c2_tx"]["status"] == "missing"
            and quantities["full_kahler_mori_cone"]["status"] == "missing"
            and quantities["equivariant_cohomology_characters"]["status"]
            == "missing",
            "reports/cicy5259_certifiability_upgrade_report.json",
            "missing full non-favourable geometry and Wilson-line character data are recorded",
        ),
    }
    return {
        "scope": "CICY5259 certifiability upgrade report",
        "conclusion": {
            "status": "partial_ambient_certification_layer_only",
            "full_nonfavourable_candidate_certified": False,
            "ambient_restricted_breadcrumb_certified": True,
            "rank_defect_h11_minus_num_projective_factors": rank_defect,
            "primary_blocker": "CICY5259 has h11=7 but only six ambient divisor classes in cicylist/pyCICY; the missing Picard direction blocks full non-favourable index, anomaly, slope, cohomology, and Wilson-line certification.",
        },
        "metadata": {
            "num": meta["Num"],
            "h11": meta["H11"],
            "h21": meta["H21"],
            "eta": meta["Eta"],
            "num_projective_factors": meta["NumPs"],
            "num_polynomials": meta["NumPol"],
            "symmetry_option_count": meta["SymmetryOptionCount"],
            "free_symmetry_option_count": meta["FreeSymmetryOptionCount"],
        },
        "quantity_status": quantities,
        "pycicy_probe": pycicy,
        "same_hodge_local_inventory": same_hodge_local_inventory(),
        "ambient_restricted_breadcrumb": {
            "matrix": hit["matrix"],
            "c1_zero_in_ambient_rows": c1_zero,
            "index_v": hit["ambient_restricted_index_v"],
            "index_wedge2_v": hit["ambient_restricted_index_wedge2_v"],
            "anomaly": hit["anomaly"],
            "slope_zero_evidence": {
                "max_normalized_slope": hit["slope_search"]["max_normalized_slope"],
                "kahler_point": hit["slope_search"]["kahler_point"],
                "scope": "ambient positive orthant approximation",
            },
            "spectrum": {
                "upstairs_10": hit_spectrum["upstairs_10"],
                "upstairs_anti_10": hit_spectrum["upstairs_anti_10"],
                "upstairs_5bar": hit_spectrum["upstairs_5bar"],
                "upstairs_5": hit_spectrum["upstairs_5"],
                "expected_upstairs_chirality": hit_spectrum[
                    "expected_upstairs_chirality"
                ],
            },
            "cohomology": {
                "V": hit["cohomology_and_spectrum"]["V_cohomology"],
                "V_dual": hit["cohomology_and_spectrum"]["V_dual_cohomology"],
                "wedge2_V": hit["cohomology_and_spectrum"]["wedge2_V_cohomology"],
                "wedge2_V_dual": hit["cohomology_and_spectrum"][
                    "wedge2_V_dual_cohomology"
                ],
            },
            "quality": {
                "trivial_summand_count": hit_quality["trivial_summand_count"],
                "h0_v": hit_quality["h0_v"],
                "h0_v_dual": hit_quality["h0_v_dual"],
                "regular_nontrivial_summand_scan_style": hit_quality[
                    "regular_nontrivial_summand_scan_style"
                ],
            },
            "compatible_free_options": hit["compatible_free_options"],
            "novelty": hit["novelty"],
        },
        "trust_classification": {
            "trustworthy_now": [
                "configuration matrix",
                "ambient divisor rank and rank defect",
                "ambient restricted triple intersections",
                "ambient restricted c2(TX)",
                "ambient c1/index/anomaly arithmetic for ambient line-bundle charges",
                "pyCICY cohomology for ambient line-bundle charges",
                "raw free coordinate options and induced ambient-row action",
            ],
            "suggestive_only": [
                "treating ambient c2/anomaly as full anomaly",
                "treating ambient positive orthant slope solution as full Kahler-cone proof",
                "treating ambient line-bundle cohomology as exhaustive over Pic(X)",
                "assuming ambient-row-trivial free options imply full equivariant line-bundle lift",
                "inferring Wilson-line spectrum without actual cohomology characters",
            ],
        },
        "missing_data_and_algorithms": [
            {
                "item": "full Picard/divisor basis for CICY5259",
                "why_needed": "line-bundle charges live in Pic(X) of rank seven, not only the six ambient restrictions",
            },
            {
                "item": "full h11 triple-intersection tensor",
                "why_needed": "index, c2(V), anomaly, and slopes must include the missing divisor direction",
            },
            {
                "item": "full h11 c2(TX)",
                "why_needed": "anomaly and Riemann-Roch indices require c2 components in the full basis",
            },
            {
                "item": "Kahler/Mori cone in full basis",
                "why_needed": "slope-zero and anomaly-effectiveness need a real cone certificate",
            },
            {
                "item": "symmetry action on full Picard basis and lift obstruction checks",
                "why_needed": "ambient-row triviality is only a necessary topological check",
            },
            {
                "item": "cohomology interface for full-Picard line bundles",
                "why_needed": "current pyCICY interface computes ambient charge-vector cohomology",
            },
            {
                "item": "equivariant cohomology character decomposition",
                "why_needed": "Wilson-line descent requires the actual group action on cohomology",
            },
        ],
        "gate_checklist": gates,
        "prior_extension_report": {
            "status": extension["conclusion"]["status"],
            "artifact": "reports/nonfavourable_extension_report.json",
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# CICY 5259 Certifiability Upgrade Report",
        "",
        f"Status: `{report['conclusion']['status']}`",
        "",
        report["conclusion"]["primary_blocker"],
        "",
        "## What Is Certified Ambient-Restricted",
        "",
    ]
    hit = report["ambient_restricted_breadcrumb"]
    lines.extend(
        [
            f"- index(V), index(wedge2 V): {hit['index_v']}, {hit['index_wedge2_v']}",
            f"- anomaly: {hit['anomaly']}",
            f"- spectrum 10/anti10/5bar/5: {hit['spectrum']['upstairs_10']}/{hit['spectrum']['upstairs_anti_10']}/{hit['spectrum']['upstairs_5bar']}/{hit['spectrum']['upstairs_5']}",
            f"- h0(V), h0(V*): {hit['quality']['h0_v']}, {hit['quality']['h0_v_dual']}",
            "",
            "## Missing For Full Certification",
            "",
        ]
    )
    for item in report["missing_data_and_algorithms"]:
        lines.append(f"- {item['item']}: {item['why_needed']}")
    lines.extend(
        [
            "",
            "## Trust Boundary",
            "",
            "Trustworthy now: "
            + ", ".join(report["trust_classification"]["trustworthy_now"])
            + ".",
            "",
            "Suggestive only: "
            + ", ".join(report["trust_classification"]["suggestive_only"])
            + ".",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_certifiability_upgrade_report.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "cicy5259_certifiability_upgrade_report.md"),
    )
    args = parser.parse_args()

    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['conclusion']['status']}")
    print(
        "ambient_restricted_breadcrumb_certified="
        f"{report['conclusion']['ambient_restricted_breadcrumb_certified']}"
    )
    print(
        "full_nonfavourable_candidate_certified="
        f"{report['conclusion']['full_nonfavourable_candidate_certified']}"
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
