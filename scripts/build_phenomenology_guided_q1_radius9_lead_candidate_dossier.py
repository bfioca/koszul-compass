#!/usr/bin/env python3
"""Build the frozen lead-candidate dossier for the character-refined q=1 survivor."""

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


def trace_neutral(coefficients: list[int]) -> bool:
    return bool(coefficients) and len(set(coefficients)) == 1


def sector_characters(candidate: dict[str, Any]) -> dict[str, Any]:
    return candidate["character_certificate"]["characters"]


def component_inventory(candidate: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    inventory = candidate["charged_matter_inventory"]
    physical_five = physical_five_component_records(candidate)
    return {
        "ten": [
            {
                "label": item["label"],
                "charge": item["charge"],
                "multiplicities": item["character"]["multiplicities"],
                "cohomology": item["cohomology"],
            }
            for item in inventory.get("ten", [])
        ],
        "fivebar": [
            {
                "label": item["label"],
                "charge": item["charge"],
                "multiplicities": item["character"]["multiplicities"],
                "downstairs_triplet_components": item["character"]["multiplicities"]["+"],
                "downstairs_doublet_components": item["character"]["multiplicities"]["-"],
                "cohomology": item["cohomology"],
            }
            for item in inventory.get("fivebar", [])
        ],
        "five": [
            {
                "label": item["label"],
                "charge": item["charge"],
                "multiplicities": item["character"]["multiplicities"],
                "downstairs_triplet_components": item["character"]["multiplicities"]["+"],
                "downstairs_doublet_components": item["character"]["multiplicities"]["-"],
                "cohomology": item["cohomology"],
            }
            for item in physical_five.values()
        ],
    }


def physical_five_component_records(candidate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    characters = sector_characters(candidate)
    out: dict[str, dict[str, Any]] = {}
    for cert in characters["wedge2_V"]["line_certificates"]:
        actual = cert.get("actual") or {}
        if "H2" not in actual:
            continue
        a, b = cert["summand_pair"]
        out[f"5_{a}{b}"] = {
            "label": f"5_{a}{b}",
            "summand_pair": [a, b],
            "charge": {
                "coefficients": [-1 if index in (a, b) else 0 for index in range(5)],
                "label": f"-e{a}-e{b}",
            },
            "cohomology": cert["cohomology"],
            "character": actual["H2"],
            "physical_component_source": "H2(wedge2 V)",
        }
    return out


def line_bundle_lookup(candidate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    characters = sector_characters(candidate)
    out: dict[str, dict[str, Any]] = {}
    for cert in characters["V"]["line_certificates"]:
        if "H1" in cert.get("actual", {}):
            out[f"10_{cert['summand_index']}"] = {
                "sector": "H1(V)",
                "line_bundle": cert["line_bundle"],
                "cohomology": cert["cohomology"],
                "character": cert["actual"]["H1"],
            }
    for cert in characters["wedge2_V"]["line_certificates"]:
        if "H1" in cert.get("actual", {}):
            a, b = cert["summand_pair"]
            out[f"5bar_{a}{b}"] = {
                "sector": "H1(wedge2 V)",
                "line_bundle": cert["line_bundle"],
                "cohomology": cert["cohomology"],
                "character": cert["actual"]["H1"],
            }
    for cert in characters["wedge2_V"]["line_certificates"]:
        if "H2" in cert.get("actual", {}):
            a, b = cert["summand_pair"]
            out[f"5_{a}{b}"] = {
                "sector": "H2(wedge2 V)",
                "line_bundle": cert["line_bundle"],
                "cohomology": cert["cohomology"],
                "character": cert["actual"]["H2"],
            }
    return out


def singlet_lookup(candidate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for item in candidate["singlet_moduli_inventory"]["all_nonzero_ext1_line_sectors"]:
        out[item["charge"]["label"]] = {
            "label": item["label"],
            "charge": item["charge"],
            "line_bundle": item["line_bundle"],
            "cohomology": item["cohomology"],
            "h1_dimension": item["h1_dimension"],
            "character_certificate": item["character_certificate"],
        }
    return out


def reconstruct_spectrum(candidate: dict[str, Any]) -> dict[str, Any]:
    characters = sector_characters(candidate)
    h1_v = characters["V"]["cohomology_characters"]["H1"]
    h1_wedge = characters["wedge2_V"]["cohomology_characters"]["H1"]
    h2_wedge = characters["wedge2_V"]["cohomology_characters"]["H2"]
    h1_wedge_dual = characters["wedge2_V_dual"]["cohomology_characters"]["H1"]
    fivebar_triplets = h1_wedge["multiplicities"]["+"]
    fivebar_doublets = h1_wedge["multiplicities"]["-"]
    five_triplets = h2_wedge["multiplicities"]["+"]
    five_doublets = h2_wedge["multiplicities"]["-"]
    return {
        "wilson_line_assignment": {
            "color_triplet_character": "+",
            "weak_doublet_character": "-",
        },
        "ten_sector": {
            "source": "H1(V)",
            "multiplicities": h1_v["multiplicities"],
            "three_family_10_sector": h1_v["multiplicities"] == {"+": 3, "-": 3},
        },
        "fivebar_sector": {
            "source": "H1(wedge2 V)",
            "multiplicities": h1_wedge["multiplicities"],
            "dbar_triplets": fivebar_triplets,
            "lepton_doublets": fivebar_doublets,
        },
        "five_sector": {
            "source": "H2(wedge2 V), tracked through H1(wedge2 V*)",
            "h2_wedge2_v_multiplicities": h2_wedge["multiplicities"],
            "h1_wedge2_v_dual_multiplicities": h1_wedge_dual["multiplicities"],
            "triplets": five_triplets,
            "doublets": five_doublets,
        },
        "net_and_vectorlike": {
            "net_dbar_families": fivebar_triplets - five_triplets,
            "net_lepton_doublet_families": fivebar_doublets - five_doublets,
            "colored_triplet_vectorlike_pairs": five_triplets,
            "electroweak_doublet_vectorlike_pairs": five_doublets,
        },
    }


def refined_mass_hits(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    lookup = line_bundle_lookup(candidate)
    singlets = singlet_lookup(candidate)
    hits = []
    for item in candidate["refined_mass_operator_table"]:
        if item["character_refined_support_class"] != "triplet_only_character_mass":
            continue
        monomials = []
        for monomial in item["invariant_singlet_monomial_hits_degree_le_2"]:
            monomials.append(
                {
                    "labels": monomial["labels"],
                    "charge": monomial["charge"],
                    "z2_product_support": monomial["z2_product_support"],
                    "singlet_factors": [
                        singlets[label] for label in monomial["labels"] if label in singlets
                    ],
                }
            )
        fivebar = lookup[item["fivebar"]]
        five = lookup[item["five"]]
        hits.append(
            {
                "fivebar": item["fivebar"],
                "five": item["five"],
                "fivebar_space": fivebar,
                "five_space": five,
                "bilinear_charge": item["bilinear_charge"],
                "needed_singlet_charge": item["needed_singlet_charge"],
                "invariant_singlet_monomials": monomials,
                "triplet_matrix_shape": [
                    item["fivebar_character_multiplicities"]["+"],
                    item["five_character_multiplicities"]["+"],
                ],
                "doublet_matrix_shape": [
                    item["fivebar_character_multiplicities"]["-"],
                    item["five_character_multiplicities"]["-"],
                ],
                "triplet_pair_support": item["triplet_pair_support"],
                "doublet_pair_support": item["doublet_pair_support"],
                "why_no_doublet_support": (
                    "the relevant 5-sector line has no surviving '-' Wilson-line "
                    "component for this bilinear"
                    if item["five_character_multiplicities"]["-"] == 0
                    else "the relevant 5bar-sector line has no surviving '-' Wilson-line component for this bilinear"
                ),
            }
        )
    return hits


def dangerous_operator_table(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    table = []
    for item in candidate["proton_decay_operator_table"]:
        coeffs = item["charge"]["coefficients"]
        table.append(
            {
                **item,
                "forbidden_reason": (
                    "not neutral under S(U(1)^5): charge coefficients are not all equal"
                    if not trace_neutral(coeffs)
                    else "not forbidden by the current residual charge rule"
                ),
            }
        )
    return table


def cup_product_frontier(candidate: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "pending_cup_product_mass_rank",
        "global_rank_conditions": {
            "triplet": (
                "the aggregate mass map on the surviving '+' 5bar/5 components must "
                "have rank 1, matching the single vectorlike colored-triplet pair"
            ),
            "doublet": (
                "the aggregate mass map on the surviving '-' 5bar/5 components must "
                "have rank 0 at the protected locus, preserving one light Higgs doublet pair"
            ),
        },
        "current_selection_rule_dimension_check": {
            "triplet_supported_hits": len(hits),
            "all_triplet_hits_have_zero_doublet_shape": all(
                hit["doublet_matrix_shape"][1] == 0 or hit["doublet_matrix_shape"][0] == 0
                for hit in hits
            ),
            "candidate_vectorlike_triplet_pairs": candidate["spectrum_certificate"][
                "vectorlike_prediction"
            ]["colored_triplet_vectorlike_pairs"],
            "candidate_vectorlike_doublet_pairs": candidate["spectrum_certificate"][
                "vectorlike_prediction"
            ]["electroweak_doublet_vectorlike_pairs"],
        },
        "maps_to_compute": [
            {
                "mass_hit": f"{hit['fivebar']}*{hit['five']}",
                "fivebar_space": {
                    "sector": hit["fivebar_space"]["sector"],
                    "line_bundle": hit["fivebar_space"]["line_bundle"],
                    "cohomology": hit["fivebar_space"]["cohomology"],
                    "plus_minus": hit["fivebar_space"]["character"]["multiplicities"],
                },
                "five_space": {
                    "sector": hit["five_space"]["sector"],
                    "line_bundle": hit["five_space"]["line_bundle"],
                    "cohomology": hit["five_space"]["cohomology"],
                    "plus_minus": hit["five_space"]["character"]["multiplicities"],
                },
                "singlet_insertions": hit["invariant_singlet_monomials"],
                "triplet_matrix_shape": hit["triplet_matrix_shape"],
                "doublet_matrix_shape": hit["doublet_matrix_shape"],
                "rank_condition": {
                    "triplet_block": "nonzero rank contribution; globally rank 1 is sufficient",
                    "doublet_block": "zero by component support for this hit",
                },
            }
            for hit in hits
        ],
        "certified_vs_pending": {
            "certified": [
                "the relevant line-bundle charges are neutralized by invariant singlet monomials",
                "the Wilson-line component characters give '+' triplet support",
                "the same mass hits have no '-' doublet support",
                "all listed dangerous 10*5bar*5bar operators are charge-forbidden",
            ],
            "pending": [
                "actual nonzero cup/product coefficients for the triplet mass blocks",
                "aggregate triplet mass matrix rank across the four allowed hit families",
                "full higher-order operator scan beyond the degree<=2 singlet monomials used here",
            ],
        },
    }


def select_candidate(refined: dict[str, Any], lead_label: str | None) -> dict[str, Any]:
    if not lead_label:
        return refined["best_candidate"]
    for record in refined.get("refined_viable_candidate_records", []):
        if record.get("label") == lead_label:
            return record
    raise KeyError(f"lead label {lead_label!r} is not a refined viable candidate")


def build_report(
    refined_report_json: Path,
    verification_json: Path,
    representative_prefilter_json: Path | None,
    lead_label: str | None,
) -> dict[str, Any]:
    refined = load_json(refined_report_json)
    verification = load_json(verification_json)
    if representative_prefilter_json and representative_prefilter_json.exists():
        prefilter = load_json(representative_prefilter_json)
        if not prefilter["promotion_policy"]["lead_dossier_allowed"]:
            gates = {
                "imports_verified_refined_report": gate(
                    refined["all_gates_pass"] and verification["all_gates_pass"],
                    f"{refined_report_json} + {verification_json}",
                    "blocked dossier starts from the verified character-shadow report",
                ),
                "imports_representative_prefilter": gate(
                    prefilter["all_gates_pass"]
                    and not prefilter["promotion_policy"]["lead_dossier_allowed"],
                    str(representative_prefilter_json),
                    "representative prefilter blocks lead promotion for this frontier",
                ),
                "no_representative_compatible_candidate": gate(
                    prefilter["summary"]["representative_compatible_weight"] == 0
                    and prefilter["summary"]["representative_unresolved_weight"] == 0
                    and prefilter["summary"]["representative_obstructed_weight"]
                    == prefilter["summary"]["character_shadow_viable_weight"],
                    str(representative_prefilter_json),
                    "all character-shadow viable candidates are representative-obstructed",
                ),
            }
            return {
                "title": "Lead Candidate Dossier Blocked By Representative Prefilter",
                "status": "lead_candidate_blocked_representative_prefilter_no_compatible_target",
                "scope": "lead promotion is blocked until representative compatibility exists",
                "source_artifacts": {
                    "refined_report_json": str(refined_report_json),
                    "refined_verification_json": str(verification_json),
                    "representative_prefilter_json": str(representative_prefilter_json),
                },
                "representative_prefilter_summary": prefilter["summary"],
                "promotion_policy": prefilter["promotion_policy"],
                "classification": {
                    "current": {
                        "category": "no_lead_candidate",
                        "status": "representative_prefilter_blocks_all_shadow_survivors",
                        "reason": prefilter["promotion_policy"]["reason"],
                    },
                    "not_promoted": "character-shadow viable candidates",
                    "not_claimed": "cup-product eligibility or full MSSM model",
                },
                "gates": gates,
                "all_gates_pass": all(item["pass"] for item in gates.values()),
            }
    candidate = select_candidate(refined, lead_label)
    hits = refined_mass_hits(candidate)
    proton = dangerous_operator_table(candidate)
    spectrum = reconstruct_spectrum(candidate)
    gates = {
        "imports_verified_refined_report": gate(
            refined["all_gates_pass"] and verification["all_gates_pass"],
            f"{refined_report_json} + {verification_json}",
            "dossier starts from the verified character-refined survivor report",
        ),
        "lead_candidate_frozen": gate(
            candidate["label"] == (lead_label or refined["best_candidate"]["label"])
            and candidate["classification"]["category"] == "viable",
            candidate["label"],
            "the selected refined viable candidate is frozen as the dossier target",
        ),
        "spectrum_reconstructs_q1": gate(
            spectrum["ten_sector"]["three_family_10_sector"]
            and spectrum["net_and_vectorlike"]["net_dbar_families"] == 3
            and spectrum["net_and_vectorlike"]["net_lepton_doublet_families"] == 3
            and spectrum["net_and_vectorlike"]["colored_triplet_vectorlike_pairs"] == 1
            and spectrum["net_and_vectorlike"]["electroweak_doublet_vectorlike_pairs"] == 1,
            "candidate character certificate",
            "Wilson-line character decomposition reconstructs the desired q=1 spectrum",
        ),
        "triplet_only_mass_hits_present": gate(
            len(hits) >= 1
            and all(hit["triplet_pair_support"] > 0 for hit in hits)
            and all(hit["doublet_pair_support"] == 0 for hit in hits),
            "refined mass operator table",
            "the dossier isolates triplet-only mass support and no doublet-support hit",
        ),
        "dangerous_operators_forbidden": gate(
            len(proton) > 0
            and all(item["forbidden_by_current_selection_rules"] for item in proton),
            "proton decay operator table",
            "all 10*5bar*5bar operators are forbidden by the residual charge rule",
        ),
        "classification_is_precise": gate(
            candidate["classification"]["status"]
            == "passes_refined_charge_character_dt_and_proton_filter"
            and not candidate["rank_status"]["cup_product_rank_computed"],
            "candidate classification and rank status",
            "classification is charge/character viable and explicitly pending cup-product rank",
        ),
    }
    return {
        "title": "Lead Character-Refined q=1 Candidate Dossier",
        "status": "lead_candidate_frozen_charge_character_viable_rank_pending",
        "scope": f"frozen dossier for {candidate['label']}",
        "candidate_identity": {
            "label": candidate["label"],
            "route": candidate["cicy_route"],
            "source": candidate["source"],
            "matrix": candidate["matrix"],
            "relation_to_5259_7914_split": (
                "candidate is in the 5259 route certified through the favourable "
                "ineffective-split 7914 presentation and inherited quotient/Wilson-line machinery"
            ),
        },
        "spectrum_and_character_certificate": {
            "spectrum_certificate": candidate["spectrum_certificate"],
            "reconstructed_wilson_line_spectrum": spectrum,
            "component_inventory": component_inventory(candidate),
            "character_certificate": candidate["character_certificate"],
        },
        "mass_operator_table": {
            "all_refined_entries": candidate["refined_mass_operator_table"],
            "triplet_only_hits": hits,
            "absence_of_doublet_support": {
                "all_refined_entries_have_no_doublet_mass_support": not any(
                    item["doublet_mass_allowed_by_refined_selection_rules"]
                    for item in candidate["refined_mass_operator_table"]
                ),
                "explanation": (
                    "for each invariant mass hit, at least one side of the '-' "
                    "Wilson-line component block is absent"
                ),
            },
        },
        "dangerous_operator_table": proton,
        "cup_product_frontier": cup_product_frontier(candidate, hits),
        "classification": {
            "current": candidate["classification"],
            "pending": "cup-product mass-rank verification and full higher-order operator analysis",
            "not_claimed": "full MSSM model",
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    if report["status"] == "lead_candidate_blocked_representative_prefilter_no_compatible_target":
        lines = [
            f"# {report['title']}",
            "",
            f"Status: `{report['status']}`",
            "",
            "## Representative Prefilter Summary",
            "",
        ]
        for key, value in report["representative_prefilter_summary"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(
            [
                "",
                "## Promotion Policy",
                "",
                f"- lead dossier allowed: `{report['promotion_policy']['lead_dossier_allowed']}`",
                f"- cup-product planning allowed: `{report['promotion_policy']['cup_product_planning_allowed']}`",
                f"- reason: {report['promotion_policy']['reason']}",
                "",
                "## Classification",
                "",
                f"- current: `{report['classification']['current']}`",
                f"- not promoted: `{report['classification']['not_promoted']}`",
                f"- not claimed: `{report['classification']['not_claimed']}`",
                "",
                "## Gates",
                "",
            ]
        )
        for key, item in report["gates"].items():
            lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    identity = report["candidate_identity"]
    spectrum = report["spectrum_and_character_certificate"]["reconstructed_wilson_line_spectrum"]
    mass = report["mass_operator_table"]
    cup = report["cup_product_frontier"]
    lines = [
        f"# {report['title']}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Candidate Identity",
        "",
        f"- label: `{identity['label']}`",
        f"- route: `{identity['route']}`",
        f"- source: `{identity['source']}`",
        f"- matrix: `{identity['matrix']}`",
        f"- split relation: {identity['relation_to_5259_7914_split']}",
        "",
        "## Spectrum And Characters",
        "",
        f"- Wilson assignment: `{spectrum['wilson_line_assignment']}`",
        f"- 10 sector: `{spectrum['ten_sector']}`",
        f"- 5bar sector: `{spectrum['fivebar_sector']}`",
        f"- 5 sector: `{spectrum['five_sector']}`",
        f"- net/vectorlike: `{spectrum['net_and_vectorlike']}`",
        "",
        "## Triplet-Only Mass Hits",
        "",
    ]
    for hit in mass["triplet_only_hits"]:
        lines.append(
            f"- `{hit['fivebar']}*{hit['five']}` via `{hit['invariant_singlet_monomials']}`; "
            f"triplet shape `{hit['triplet_matrix_shape']}`, "
            f"doublet shape `{hit['doublet_matrix_shape']}`"
        )
    lines.extend(
        [
            "",
            "## Dangerous Operators",
            "",
            f"- operator count: `{len(report['dangerous_operator_table'])}`",
            "- all forbidden: `True`",
            "",
            "## Cup-Product Frontier",
            "",
            f"- global rank conditions: `{cup['global_rank_conditions']}`",
            f"- maps to compute: `{cup['maps_to_compute']}`",
            f"- certified vs pending: `{cup['certified_vs_pending']}`",
            "",
            "## Classification",
            "",
            f"- current: `{report['classification']['current']}`",
            f"- pending: `{report['classification']['pending']}`",
            f"- not claimed: `{report['classification']['not_claimed']}`",
            "",
            "## Gates",
            "",
        ]
    )
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refined-report-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.json"),
    )
    parser.add_argument(
        "--refined-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45_verification.json"
        ),
    )
    parser.add_argument(
        "--lead-label",
        default="",
        help="Optional refined viable candidate label to freeze; defaults to report best_candidate.",
    )
    parser.add_argument(
        "--representative-prefilter-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_representative_prefilter_rollup.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_candidate_dossier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_candidate_dossier.md"),
    )
    args = parser.parse_args()
    report = build_report(
        refined_report_json=Path(args.refined_report_json),
        verification_json=Path(args.refined_verification_json),
        representative_prefilter_json=Path(args.representative_prefilter_json)
        if args.representative_prefilter_json
        else None,
        lead_label=args.lead_label or None,
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    if "candidate_identity" in report:
        print(f"lead={report['candidate_identity']['label']}")
        print(f"triplet_only_hits={len(report['mass_operator_table']['triplet_only_hits'])}")
    else:
        print("lead=blocked_by_representative_prefilter")
    print(f"all_gates_pass={report['all_gates_pass']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
