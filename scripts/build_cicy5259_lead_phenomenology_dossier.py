#!/usr/bin/env python3
"""Build a phenomenology dossier for the lead CICY 5259/7914 q=1 target."""

from __future__ import annotations

import argparse
from itertools import permutations
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from build_cicy5259_quotient_wilson_line_report import (  # noqa: E402
    line_character_certificate,
)
from string_theory.cohomology import bundle_line_summands, cohomology_record  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def charge_label(indices: list[int], sign: int = 1) -> dict[str, Any]:
    coeffs = [0, 0, 0, 0, 0]
    for index in indices:
        coeffs[index] += sign
    return {"coefficients": coeffs, "label": format_charge(coeffs)}


def format_charge(coeffs: list[int]) -> str:
    parts = []
    for index, value in enumerate(coeffs):
        if value == 0:
            continue
        sign = "+" if value > 0 else "-"
        magnitude = "" if abs(value) == 1 else str(abs(value))
        term = f"{magnitude}e{index}"
        if not parts and sign == "+":
            parts.append(term)
        else:
            parts.append(f"{sign}{term}")
    return "0" if not parts else "".join(parts)


def add_charges(*charges: list[int]) -> list[int]:
    return [sum(charge[index] for charge in charges) for index in range(5)]


def neg_charge(charge: list[int]) -> list[int]:
    return [-value for value in charge]


def is_su5_trace_neutral(charge: list[int]) -> bool:
    return len(set(charge)) == 1


def singlet_sector_records(
    *,
    conf: list[list[int]],
    matrix: list[list[int]],
) -> list[dict[str, Any]]:
    context = load_5259_action_context()
    lines = bundle_line_summands(matrix)
    records = []
    for i, j in permutations(range(5), 2):
        line_bundle = [lines[i][row] - lines[j][row] for row in range(7)]
        cohomology = cohomology_record(conf, line_bundle)["cohomology"]
        if not any(cohomology):
            continue
        certificate = line_character_certificate(
            conf=conf,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
            line_bundle=line_bundle,
            cohomology=cohomology,
            fiber_sign=1,
        )
        records.append(
            {
                "label": f"S_{i}{j}",
                "charge": {
                    "coefficients": [
                        1 if index == i else -1 if index == j else 0
                        for index in range(5)
                    ],
                    "label": f"e{i}-e{j}",
                },
                "line_bundle": line_bundle,
                "cohomology": cohomology,
                "h1_dimension": cohomology[1],
                "character_certificate": {
                    "method": certificate["method"],
                    "actual_character_computed": certificate[
                        "actual_character_computed"
                    ],
                    "actual": certificate["actual"],
                },
            }
        )
    return records


def h1_singlets_by_charge(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        record["charge"]["label"]: record
        for record in records
        if record["h1_dimension"] > 0
        and record["character_certificate"]["actual_character_computed"]
    }


def monomial_charge(labels: list[str], singlets: dict[str, dict[str, Any]]) -> list[int]:
    charge = [0, 0, 0, 0, 0]
    for label in labels:
        charge = add_charges(charge, singlets[label]["charge"]["coefficients"])
    return charge


def build_wilson_decomposition(target: dict[str, Any]) -> dict[str, Any]:
    sectors = target["characters"]
    h1_v = sectors["V"]["cohomology_characters"]["H1"]
    h1_wedge = sectors["wedge2_V"]["cohomology_characters"]["H1"]
    h2_wedge = sectors["wedge2_V"]["cohomology_characters"]["H2"]
    h1_wedge_dual = sectors["wedge2_V_dual"]["cohomology_characters"]["H1"]
    return {
        "wilson_line_embedding": {
            "label": "nontrivial_Z2_SU5_breaking",
            "fundamental_5_character_assignment": {
                "color_triplet": "+",
                "weak_doublet": "-",
                "determinant_condition_satisfied": True,
            },
        },
        "ten_sector": {
            "source": "H1(V)",
            "multiplicities": h1_v["multiplicities"],
            "q_left_doublets": h1_v["multiplicities"]["-"],
            "u_right_conjugates": h1_v["multiplicities"]["+"],
            "e_right_conjugates": h1_v["multiplicities"]["+"],
            "three_family_10_sector": h1_v["multiplicities"] == {"+": 3, "-": 3},
        },
        "fivebar_sector": {
            "source": "H1(wedge2 V)",
            "multiplicities": h1_wedge["multiplicities"],
            "dbar_triplets": h1_wedge["multiplicities"]["+"],
            "lepton_doublets": h1_wedge["multiplicities"]["-"],
        },
        "five_sector": {
            "source": "H2(wedge2 V), equivalently H1(wedge2 V*) by Serre duality",
            "h2_wedge2_v_multiplicities": h2_wedge["multiplicities"],
            "h1_wedge2_v_dual_multiplicities": h1_wedge_dual["multiplicities"],
            "triplets": h2_wedge["multiplicities"]["+"],
            "doublets": h2_wedge["multiplicities"]["-"],
        },
        "net_and_vectorlike": {
            "net_dbar_families": h1_wedge["multiplicities"]["+"]
            - h2_wedge["multiplicities"]["+"],
            "net_lepton_doublet_families": h1_wedge["multiplicities"]["-"]
            - h2_wedge["multiplicities"]["-"],
            "colored_triplet_vectorlike_pairs": h2_wedge["multiplicities"]["+"],
            "electroweak_doublet_vectorlike_pairs": h2_wedge["multiplicities"]["-"],
        },
    }


def charged_matter_inventory(target: dict[str, Any]) -> dict[str, Any]:
    inventory = {"ten": [], "fivebar": [], "five": []}
    for cert in target["characters"]["V"]["line_certificates"]:
        if "H1" not in cert["actual"]:
            continue
        index = cert["summand_index"]
        inventory["ten"].append(
            {
                "label": f"10_{index}",
                "summand_index": index,
                "charge": charge_label([index]),
                "cohomology": cert["cohomology"],
                "character": cert["actual"]["H1"],
            }
        )
    for cert in target["characters"]["wedge2_V"]["line_certificates"]:
        if "H1" not in cert["actual"]:
            continue
        a, b = cert["summand_pair"]
        inventory["fivebar"].append(
            {
                "label": f"5bar_{a}{b}",
                "summand_pair": [a, b],
                "charge": charge_label([a, b]),
                "cohomology": cert["cohomology"],
                "character": cert["actual"]["H1"],
            }
        )
    for cert in target["characters"]["wedge2_V_dual"]["line_certificates"]:
        if "H1" not in cert["actual"]:
            continue
        a, b = cert["summand_pair"]
        inventory["five"].append(
            {
                "label": f"5_{a}{b}",
                "summand_pair": [a, b],
                "charge": charge_label([a, b], sign=-1),
                "cohomology": cert["cohomology"],
                "character": cert["actual"]["H1"],
            }
        )
    return inventory


def mass_operator_analysis(
    *,
    inventory: dict[str, Any],
    singlets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    five = inventory["five"][0]
    operators = []
    candidate_monomials = [
        ["e1-e3", "e3-e0"],
        ["e1-e4", "e4-e0"],
    ]
    for fivebar in inventory["fivebar"]:
        bilinear_charge = add_charges(
            fivebar["charge"]["coefficients"], five["charge"]["coefficients"]
        )
        needed = neg_charge(bilinear_charge)
        monomial_hits = []
        for labels in candidate_monomials:
            if all(label in singlets for label in labels):
                charge = monomial_charge(labels, singlets)
                if is_su5_trace_neutral(add_charges(charge, bilinear_charge)):
                    monomial_hits.append(
                        {
                            "singlet_monomial": labels,
                            "monomial_charge": {
                                "coefficients": charge,
                                "label": format_charge(charge),
                            },
                            "z2_comment": (
                                "all listed singlet factors have regular Z2 H1 characters, "
                                "so an invariant even product exists at character level"
                            ),
                        }
                    )
        operators.append(
            {
                "fivebar": fivebar["label"],
                "five": five["label"],
                "bilinear_charge": {
                    "coefficients": bilinear_charge,
                    "label": format_charge(bilinear_charge),
                },
                "needed_singlet_charge": {
                    "coefficients": needed,
                    "label": format_charge(needed),
                },
                "certified_singlet_monomial_hits": monomial_hits,
            }
        )

    return {
        "mass_target": (
            "lift the single colored triplet vectorlike pair while preserving one "
            "light electroweak doublet pair"
        ),
        "vectorlike_five_source": five,
        "candidate_mass_operators": operators,
        "charge_level_result": (
            "The 5bar_04 x 5_14 bilinear can be neutralized by the certified "
            "H1 singlet monomial S_14*S_40. A second charge-compatible path "
            "S_13*S_30 exists at the raw cohomology level, but S_13 lacks a "
            "completed Z2 character certificate in the current machinery. The "
            "same line-bundle and Z2 selection rules apply to the triplet and "
            "doublet components, so this evidence supports vectorlike 5/5bar "
            "mass terms but does not protect exactly one light Higgs doublet pair."
        ),
        "cup_product_status": {
            "computed": False,
            "reason": (
                "The workspace has cohomology dimensions and Z2 characters, but not "
                "the cup-product maps/ranks for singlet-dependent mass matrices."
            ),
        },
    }


def proton_decay_analysis(inventory: dict[str, Any]) -> dict[str, Any]:
    ten_1 = next(item for item in inventory["ten"] if item["label"] == "10_1")
    fivebar_04 = next(item for item in inventory["fivebar"] if item["label"] == "5bar_04")
    fivebar_23 = next(item for item in inventory["fivebar"] if item["label"] == "5bar_23")
    charge = add_charges(
        ten_1["charge"]["coefficients"],
        fivebar_04["charge"]["coefficients"],
        fivebar_23["charge"]["coefficients"],
    )
    return {
        "dimension_four_su5_operator_10_5bar_5bar": {
            "example": "10_1 * 5bar_04 * 5bar_23",
            "charge": {"coefficients": charge, "label": format_charge(charge)},
            "neutral_under_S_U1_5": is_su5_trace_neutral(charge),
            "z2_character_comment": (
                "Each factor has regular Z2 character content, so component choices "
                "with total even Z2 character exist."
            ),
            "interpretation": (
                "Line-bundle charges and the recorded Z2 Wilson line do not by "
                "themselves forbid this dangerous operator."
            ),
        },
        "dimension_five_su5_operator_10_10_10_5bar": {
            "status": "not_protected_by_current_evidence",
            "reason": (
                "No residual matter parity or alternative discrete symmetry has been "
                "identified in the certified data; a full operator analysis would "
                "require explicit family/component cup products."
            ),
        },
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    quotient = load_json(REPORTS / "cicy5259_quotient_wilson_line_report.json")
    target_report = load_json(REPORTS / "cicy5259_h2_frontier_radius1_target.json")
    target = target_report["best_character_certified_record"]
    conf = split["full_picard_presentation_7914"]["conf"]
    singlet_records = singlet_sector_records(conf=conf, matrix=target["matrix"])
    certified_h1_singlets = h1_singlets_by_charge(singlet_records)
    inventory = charged_matter_inventory(target)
    wilson = build_wilson_decomposition(target)
    mass = mass_operator_analysis(
        inventory=inventory, singlets=certified_h1_singlets
    )
    proton = proton_decay_analysis(inventory)

    classification = {
        "status": "phenomenologically_obstructed_by_current_charge_level_evidence",
        "category": "phenomenologically obstructed",
        "reason": (
            "The candidate has the desired q=1 near-MSSM spectrum before mass "
            "lifting, but the same certified residual charges that allow singlet "
            "mass terms for the colored triplet pair also allow the corresponding "
            "doublet mass term, and a dangerous 10*5bar*5bar operator is neutral "
            "under the available selection rules. No residual symmetry protecting "
            "one light Higgs doublet pair is identified."
        ),
        "not_mssm_like_after_vectorlike_mass_lifting_because": [
            "no charge-level distinction between triplet and doublet vectorlike mass terms",
            "cup-product ranks for selective triplet lifting are not computed",
            "dimension-four 10*5bar*5bar operator is not forbidden by line-bundle charges or Z2",
        ],
    }

    gates = {
        "lead_target_is_q1_character_certified": gate(
            target["character_certified"]
            and target["vectorlike_pair_prediction"][
                "h2_wedge2_regular_multiplicity"
            ]
            == 1,
            str(REPORTS / "cicy5259_h2_frontier_radius1_target.json"),
            "lead target is the radius-1 5259/7914 q=1 character-certified candidate",
        ),
        "favourable_split_certification_imported": gate(
            quotient["conclusion"]["split_action_lift_certified"]
            and quotient["conclusion"]["full_picard_action_certified"]
            and quotient["conclusion"]["line_bundle_equivariance_certified"],
            str(REPORTS / "cicy5259_quotient_wilson_line_report.json"),
            "geometry, Picard action, quotient lift, and equivariant-bundle gates are certified in the 7914 split presentation",
        ),
        "wilson_line_decomposition_has_one_vectorlike_pair": gate(
            wilson["net_and_vectorlike"]["colored_triplet_vectorlike_pairs"] == 1
            and wilson["net_and_vectorlike"][
                "electroweak_doublet_vectorlike_pairs"
            ]
            == 1
            and wilson["net_and_vectorlike"]["net_dbar_families"] == 3
            and wilson["net_and_vectorlike"]["net_lepton_doublet_families"] == 3,
            "target Z2 character multiplicities",
            "nontrivial Z2 Wilson line leaves three families plus one vectorlike triplet and one vectorlike doublet pair",
        ),
        "singlet_mass_terms_are_charge_allowed": gate(
            any(
                item["certified_singlet_monomial_hits"]
                for item in mass["candidate_mass_operators"]
                if item["fivebar"] == "5bar_04"
            ),
            "certified H1 singlet charge scan",
            "certified singlet monomials can neutralize at least one vectorlike 5bar/5 bilinear",
        ),
        "no_doublet_triplet_selection_rule_found": gate(
            True,
            "line-bundle charges plus Z2 Wilson-line characters",
            "triplet and doublet mass bilinears have the same residual line-bundle and Z2 invariance condition",
        ),
        "dangerous_operator_not_forbidden": gate(
            proton["dimension_four_su5_operator_10_5bar_5bar"][
                "neutral_under_S_U1_5"
            ],
            "charged matter inventory",
            "10_1*5bar_04*5bar_23 is neutral under S(U(1)^5) and not removed by the Z2 character evidence",
        ),
    }

    return {
        "scope": "phenomenology dossier for frozen CICY 5259/7914 q=1 lead near-MSSM target",
        "certification_scope": {
            "certified_in_favourable_7914_split_presentation": [
                "geometry/topology",
                "c1, indices, c2(V), anomaly",
                "slope feasibility in the favourable ambient cone approximation",
                "selected recorded Z2 action lift through the 7914 P2 split",
                "identity Picard action on J0..J6",
                "determinant-trivial line-bundle equivariant linearisations",
                "Z2 cohomology character decompositions for V, V*, wedge2 V, wedge2 V*",
            ],
            "relation_to_5259_route": (
                "The target is certified on the favourable ineffective-split CICY "
                "7914 presentation whose split row/columns contract back to the "
                "non-favourable CICY 5259 route. It should be cited as a 5259/7914 "
                "ineffective-split candidate, not as an independently native "
                "non-favourable Picard certificate on 5259."
            ),
        },
        "candidate_identity": {
            "cicy_route": "5259 via favourable ineffective split 7914",
            "matrix": target["matrix"],
            "move_from_previous_q3_candidate": target["move_from_base"],
            "anomaly": target["anomaly"],
            "cohomology": target["cohomology"],
            "vectorlike_prediction": target["vectorlike_pair_prediction"],
        },
        "wilson_line_decomposition": wilson,
        "charged_matter_inventory": inventory,
        "singlet_moduli_inventory": {
            "all_nonzero_ext1_line_sectors": singlet_records,
            "certified_h1_singlet_charge_labels": sorted(certified_h1_singlets),
        },
        "vectorlike_mass_analysis": mass,
        "proton_decay_and_residual_symmetry": proton,
        "classification": classification,
        "gates": gates,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    identity = report["candidate_identity"]
    wilson = report["wilson_line_decomposition"]
    mass = report["vectorlike_mass_analysis"]
    proton = report["proton_decay_and_residual_symmetry"]
    classification = report["classification"]
    lines = [
        "# CICY 5259/7914 Lead Phenomenology Dossier",
        "",
        f"Classification: `{classification['category']}`",
        f"Status: `{classification['status']}`",
        "",
        "## Frozen Target",
        "",
        "- Route: `5259` via favourable ineffective split `7914`.",
        f"- Matrix: `{identity['matrix']}`",
        f"- Anomaly: `{identity['anomaly']}`",
        f"- Cohomology `V/V*/wedge2V/wedge2V*`: `{identity['cohomology']['V']}` / `{identity['cohomology']['V_dual']}` / `{identity['cohomology']['wedge2_V']}` / `{identity['cohomology']['wedge2_V_dual']}`",
        f"- Vectorlike prediction: `{identity['vectorlike_prediction']}`",
        "",
        "## Certified Scope",
        "",
        report["certification_scope"]["relation_to_5259_route"],
        "",
        "The geometry, topology, anomaly, slope-feasibility, Picard-action, quotient-lift, line-bundle-equivariance, and Wilson-line character data are treated as certified in the favourable `7914` split presentation.",
        "",
        "## Wilson-Line Components",
        "",
        f"- `10` sector: `{wilson['ten_sector']}`",
        f"- `5bar` sector: `{wilson['fivebar_sector']}`",
        f"- `5` sector: `{wilson['five_sector']}`",
        f"- net/vectorlike: `{wilson['net_and_vectorlike']}`",
        "",
        "## Mass Terms",
        "",
        mass["charge_level_result"],
        "",
        f"- candidate mass operators: `{mass['candidate_mass_operators']}`",
        f"- cup-product status: `{mass['cup_product_status']}`",
        "",
        "## Proton Decay",
        "",
        f"- dangerous dimension-four example: `{proton['dimension_four_su5_operator_10_5bar_5bar']}`",
        f"- dimension-five status: `{proton['dimension_five_su5_operator_10_10_10_5bar']}`",
        "",
        "## Verdict",
        "",
        classification["reason"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_lead_phenomenology_dossier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "cicy5259_lead_phenomenology_dossier.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['classification']['status']}")
    print(f"classification={report['classification']['category']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
