#!/usr/bin/env python3
"""Build a dossier for the first higher-degree 5259/7914 selection candidate.

The higher-degree intersection scan found representative-compatible
triplet-only selection candidates after allowing singlet monoids of degree
2/3.  This dossier freezes the first stable lead and states the next algebraic
question without promoting it to a simple CY3 cubic cup-product certificate.
"""

from __future__ import annotations

import argparse
from collections import Counter
from itertools import permutations
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_filter_report import (  # noqa: E402
    add_charges,
    format_charge,
    is_su5_trace_neutral,
)
from build_phenomenology_guided_q1_radius9_character_refined_dt_report import (  # noqa: E402
    full_candidate_record,
    source_records,
)
from string_theory.cohomology import cohomology_record  # noqa: E402


EXPECTED_LEAD = "radius6_broad_adjacency_filtered_10_branch_50"
EXPECTED_OPERATOR = "5bar_02*5_34"
EXPECTED_FIVEBAR = "5bar_02"
EXPECTED_FIVE = "5_34"
EXPECTED_MONOMIAL_LABELS = ["e3-e2", "e4-e0"]
ZERO_LINE = [0, 0, 0, 0, 0, 0, 0]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def vector_sum(*vectors: list[int]) -> list[int]:
    if not vectors:
        return []
    return [sum(vector[index] for vector in vectors) for index in range(len(vectors[0]))]


def neg_vector(vector: list[int]) -> list[int]:
    return [-value for value in vector]


def pair_from_label(prefix: str, label: str) -> list[int]:
    raw = label.removeprefix(prefix)
    return [int(raw[0]), int(raw[1])]


def find_source_candidate(label: str) -> tuple[dict[str, Any], int, dict[str, Any]]:
    for source, weight, record in source_records(45):
        if record.get("label") == label:
            candidate = full_candidate_record(
                source=source,
                weight=weight,
                record=record,
                mass_table=[],
                classification=record.get("classification", {}),
            )
            return source, weight, candidate
    raise KeyError(f"source candidate not found: {label}")


def find_lead(higher_degree_report: dict[str, Any]) -> dict[str, Any]:
    for lead in higher_degree_report["lead_candidates"]:
        if (
            lead["candidate_label"] == EXPECTED_LEAD
            and lead["operator"] == EXPECTED_OPERATOR
            and lead["sample_compatible_monomial_hits"][0]["labels"]
            == EXPECTED_MONOMIAL_LABELS
        ):
            return lead
    raise KeyError(f"higher-degree lead not found: {EXPECTED_LEAD}")


def find_pair_certificate(
    *, candidate: dict[str, Any], sector: str, pair: list[int]
) -> dict[str, Any]:
    for cert in candidate["character_certificate"]["characters"][sector][
        "line_certificates"
    ]:
        if cert.get("summand_pair") == pair:
            return cert
    raise KeyError(f"missing {sector} pair certificate: {pair}")


def find_inventory_item(
    *, inventory: dict[str, list[dict[str, Any]]], sector: str, label: str
) -> dict[str, Any]:
    for item in inventory[sector]:
        if item["label"] == label:
            return item
    raise KeyError(f"missing {sector} inventory item: {label}")


def find_singlet(candidate: dict[str, Any], charge_label: str) -> dict[str, Any]:
    for item in candidate["singlet_moduli_inventory"][
        "all_nonzero_ext1_line_sectors"
    ]:
        if item["charge"]["label"] == charge_label:
            return item
    raise KeyError(f"missing singlet charge label: {charge_label}")


def compact_character(character: dict[str, Any]) -> dict[str, Any]:
    return {
        "dimension": character["dimension"],
        "multiplicities": character["multiplicities"],
        "nonidentity_trace": character["nonidentity_trace"],
        "regular_multiplicity": character.get("regular_multiplicity"),
    }


def compact_leg(
    *,
    role: str,
    label: str,
    line_bundle: list[int],
    charge: dict[str, Any],
    cohomology: list[int],
    h_degree: int,
    representative: dict[str, Any],
    character: dict[str, Any],
    method: str | None,
) -> dict[str, Any]:
    return {
        "role": role,
        "label": label,
        "line_bundle": line_bundle,
        "charge": charge,
        "cohomology": cohomology,
        "cohomology_degree_used": h_degree,
        "representative": representative,
        "character": compact_character(character),
        "character_method": method,
    }


def prefix_proxy(
    *, conf: list[list[int]], legs: list[dict[str, Any]]
) -> dict[str, Any]:
    ordering_records = []
    prefix_hits_by_length: Counter[str] = Counter()
    sample_nonzero_prefixes = []
    for ordered in permutations(legs):
        running = [0] * len(legs[0]["line_bundle"])
        prefixes = []
        for length, leg in enumerate(ordered, start=1):
            running = vector_sum(running, leg["line_bundle"])
            if length <= 3:
                cohomology = cohomology_record(conf, running)["cohomology"]
                target_dimension = cohomology[length]
                target_group = f"H{length}"
            else:
                cohomology = None
                target_dimension = None
                target_group = "H4(outside_CY3_range)"
            prefix = {
                "length": length,
                "labels": [item["label"] for item in ordered[:length]],
                "line_bundle_sum": running,
                "ordinary_target_group": target_group,
                "ordinary_target_dimension": target_dimension,
                "ordinary_target_cohomology": cohomology,
            }
            prefixes.append(prefix)
            if target_dimension and target_dimension > 0:
                prefix_hits_by_length[str(length)] += 1
                if len(sample_nonzero_prefixes) < 8:
                    sample_nonzero_prefixes.append(prefix)
        ordering_records.append(
            {
                "ordering": [item["label"] for item in ordered],
                "prefixes": prefixes,
            }
        )
    return {
        "total_orderings": len(ordering_records),
        "ordinary_nonzero_prefix_counts_by_length": dict(
            sorted(prefix_hits_by_length.items())
        ),
        "sample_nonzero_prefixes": sample_nonzero_prefixes,
        "all_length_three_prefixes_have_zero_H3": not any(
            record["prefixes"][2]["ordinary_target_dimension"]
            for record in ordering_records
        ),
        "all_orderings_end_in_H4_outside_CY3": all(
            record["prefixes"][3]["ordinary_target_group"] == "H4(outside_CY3_range)"
            for record in ordering_records
        ),
        "ordering_records": ordering_records,
    }


def build_report(
    *,
    higher_degree_json: Path,
    higher_degree_verification_json: Path,
    split_json: Path,
) -> dict[str, Any]:
    higher_degree = load_json(higher_degree_json)
    higher_degree_verification = load_json(higher_degree_verification_json)
    split = load_json(split_json)
    conf = split["full_picard_presentation_7914"]["conf"]
    ox = cohomology_record(conf, ZERO_LINE)
    lead = find_lead(higher_degree)
    source, weight, candidate = find_source_candidate(lead["candidate_label"])
    fivebar_item = find_inventory_item(
        inventory=candidate["charged_matter_inventory"],
        sector="fivebar",
        label=EXPECTED_FIVEBAR,
    )
    five_item = find_inventory_item(
        inventory=candidate["charged_matter_inventory"],
        sector="five",
        label=EXPECTED_FIVE,
    )
    fivebar_cert = find_pair_certificate(
        candidate=candidate,
        sector="wedge2_V",
        pair=pair_from_label("5bar_", EXPECTED_FIVEBAR),
    )
    five_cup_cert = find_pair_certificate(
        candidate=candidate,
        sector="wedge2_V_dual",
        pair=pair_from_label("5_", EXPECTED_FIVE),
    )
    singlets = [find_singlet(candidate, label) for label in EXPECTED_MONOMIAL_LABELS]
    singlet_line_sum = vector_sum(*(item["line_bundle"] for item in singlets))
    total_charge = add_charges(
        fivebar_item["charge"]["coefficients"],
        five_item["charge"]["coefficients"],
        *(item["charge"]["coefficients"] for item in singlets),
    )
    total_line = vector_sum(
        fivebar_cert["line_bundle"],
        five_cup_cert["line_bundle"],
        *(item["line_bundle"] for item in singlets),
    )
    bilinear_charge = add_charges(
        fivebar_item["charge"]["coefficients"],
        five_item["charge"]["coefficients"],
    )
    bilinear_line = vector_sum(fivebar_cert["line_bundle"], five_cup_cert["line_bundle"])
    legs = [
        compact_leg(
            role="physical_5bar_H1_wedge2_V",
            label=EXPECTED_FIVEBAR,
            line_bundle=fivebar_cert["line_bundle"],
            charge=fivebar_item["charge"],
            cohomology=fivebar_cert["cohomology"],
            h_degree=1,
            representative=lead["fivebar_representative"],
            character=fivebar_cert["actual"]["H1"],
            method=fivebar_cert["method"],
        ),
        compact_leg(
            role="cup_dual_5_H1_wedge2_V_dual",
            label=EXPECTED_FIVE,
            line_bundle=five_cup_cert["line_bundle"],
            charge=five_item["charge"],
            cohomology=five_cup_cert["cohomology"],
            h_degree=1,
            representative=lead["five_cup_representative"],
            character=five_cup_cert["actual"]["H1"],
            method=five_cup_cert["method"],
        ),
    ]
    for singlet, representative in zip(singlets, lead["first_singlet_representatives"]):
        legs.append(
            compact_leg(
                role="h1_singlet_insertion",
                label=singlet["charge"]["label"],
                line_bundle=singlet["line_bundle"],
                charge=singlet["charge"],
                cohomology=singlet["cohomology"],
                h_degree=1,
                representative=representative,
                character=singlet["character_certificate"]["actual"]["H1"],
                method=singlet["character_certificate"]["method"],
            )
        )

    prefix = prefix_proxy(conf=conf, legs=legs)
    proton_table = candidate["proton_decay_operator_table"]
    forbidden_proton_count = sum(
        1 for item in proton_table if item["forbidden_by_current_selection_rules"]
    )
    mass_tensor_frontier = {
        "operator": EXPECTED_OPERATOR,
        "monomial": EXPECTED_MONOMIAL_LABELS,
        "field_count": 4,
        "ordinary_h1_degree_sum": 4,
        "ordinary_cup_status": "not_a_simple_CY3_cubic_top_product",
        "ordinary_cup_reason": (
            "Four H1 factors would land in H4(O_X) under the ordinary cup product, "
            "while a CY3 superpotential integral is controlled by H3(O_X)."
        ),
        "higher_order_question": (
            "Compute the effective quartic/Yoneda-Massey/A-infinity mass tensor "
            "with singlet vevs in H1(e3-e2) and H1(e4-e0), then project the "
            "triplet and doublet Wilson-line component blocks."
        ),
        "triplet_mass_block": {
            "selection_rule_shape": [
                lead["fivebar_representative"]["computed_signature"],
                lead["five_cup_representative"]["computed_signature"],
            ],
            "matrix_dimensions_after_fixed_singlet_vevs": [1, 1],
            "rank_needed_to_lift_colored_triplet_pair": 1,
            "rank_status": "pending_higher_order_mass_map",
        },
        "doublet_mass_block": {
            "selection_rule_shape": [
                fivebar_item["character"]["multiplicities"]["-"],
                five_item["character"]["multiplicities"]["-"],
            ],
            "matrix_dimensions_after_fixed_singlet_vevs": [
                fivebar_item["character"]["multiplicities"]["-"],
                five_item["character"]["multiplicities"]["-"],
            ],
            "rank_needed_to_preserve_light_doublet_pair": 0,
            "rank_status": "selection_rule_forces_zero_for_this_operator",
        },
        "minimal_engine_requirements": [
            "construct equivariant Koszul/Cech representatives for the four H1 legs",
            "implement multiplication plus homotopy/projection in the Koszul total complex",
            "evaluate the order-4 effective product or equivalent Massey/Yoneda representative",
            "insert singlet vev directions in the even invariant component of H1(e3-e2) x H1(e4-e0)",
            "compute the resulting 1x1 triplet block and confirm the doublet block remains zero",
        ],
    }
    verdict = {
        "status": "higher_order_mass_map_pending_for_frozen_candidate",
        "classification": "representative-compatible higher-degree selection candidate",
        "certified_facts": [
            "q=1 three-family spectrum is present in the audited radius-9 frontier",
            "physical 5bar H1, cup-dual 5 H1, and both singlet H1 factors are representative-compatible",
            "the selected degree-2 singlet monoid is charge-neutralizing and Z2-even at component level",
            "the operator has triplet support 1, doublet support 0, and zero dangerous 10*5bar*5bar hits under current selection rules",
        ],
        "pending_assumptions": [
            "nonzero higher-order effective mass tensor",
            "choice of singlet vev directions with nonzero triplet coupling",
            "absence of additional higher-order proton or doublet couplings beyond the current selection table",
        ],
        "not_claimed": "simple CY3 cubic cup-product mass-rank verification",
    }
    gates = {
        "starts_from_verified_higher_degree_search": gate(
            higher_degree["all_gates_pass"]
            and higher_degree_verification["all_gates_pass"]
            and higher_degree["status"] == "higher_degree_intersection_candidate_found",
            f"{higher_degree_json} + {higher_degree_verification_json}",
            "dossier imports the verified higher-degree intersection search",
        ),
        "frozen_lead_identity_is_stable": gate(
            lead["candidate_label"] == EXPECTED_LEAD
            and lead["operator"] == EXPECTED_OPERATOR
            and lead["sample_compatible_monomial_hits"][0]["labels"]
            == EXPECTED_MONOMIAL_LABELS
            and source == lead["source"]
            and weight == lead["weight"],
            EXPECTED_LEAD,
            "first higher-degree lead identity, operator, monomial, source, and weight match",
        ),
        "q1_spectrum_is_reconstructed": gate(
            candidate["cicy_route"] == "5259/7914"
            and candidate["spectrum_certificate"]["desired_q1_three_family_signature"]
            and candidate["spectrum_certificate"]["cohomology"]["V"] == [0, 6, 0, 0]
            and candidate["spectrum_certificate"]["cohomology"]["wedge2_V"]
            == [0, 8, 2, 0]
            and candidate["spectrum_certificate"]["vectorlike_prediction"][
                "colored_triplet_vectorlike_pairs"
            ]
            == 1
            and candidate["spectrum_certificate"]["vectorlike_prediction"][
                "electroweak_doublet_vectorlike_pairs"
            ]
            == 1,
            "source candidate spectrum_certificate",
            "source record reconstructs the q=1 three-family plus one vectorlike pair signature",
        ),
        "representative_stack_is_compatible": gate(
            lead["fivebar_representative"]["status"] == "representative_compatible"
            and lead["fivebar_representative"]["computed_signature"] == "+1/-1"
            and lead["five_cup_representative"]["status"]
            == "representative_compatible"
            and lead["five_cup_representative"]["computed_signature"] == "+1/-0"
            and [item["computed_signature"] for item in lead["first_singlet_representatives"]]
            == ["+6/-6", "+2/-2"],
            "lead representative stack",
            "physical 5bar, cup 5, and singlet factors have representative-compatible characters",
        ),
        "charge_and_line_bundle_neutrality_hold": gate(
            total_charge == [0, 0, 0, 0, 0]
            and is_su5_trace_neutral(total_charge)
            and total_line == ZERO_LINE
            and singlet_line_sum == neg_vector(bilinear_line),
            str({"charge": total_charge, "line": total_line}),
            "degree-2 singlet monoid neutralizes both SU(5) charge vector and 7914 line-bundle class",
        ),
        "triplet_only_and_proton_safe_selection_stack": gate(
            lead["triplet_pair_support"] == 1
            and lead["doublet_pair_support"] == 0
            and lead["proton_allowed_count"] == 0
            and forbidden_proton_count == len(proton_table),
            str(lead),
            "current selection rules give triplet-only support and forbid every listed dangerous proton operator",
        ),
        "ordinary_cubic_cup_not_overclaimed": gate(
            not lead["simple_cy3_cubic_top_cup_eligible"]
            and lead["higher_order_mass_map_pending"]
            and ox["cohomology"] == [1, 0, 0, 1]
            and mass_tensor_frontier["ordinary_h1_degree_sum"] == 4
            and prefix["all_orderings_end_in_H4_outside_CY3"],
            "ordinary cup degree audit",
            "the dossier keeps the lead at higher-order pending status, not cubic cup-product rank status",
        ),
    }
    report = {
        "title": "Higher-Degree Candidate Dossier",
        "scope": f"{EXPECTED_LEAD}: {EXPECTED_OPERATOR} with {EXPECTED_MONOMIAL_LABELS}",
        "status": verdict["status"],
        "source_artifacts": {
            "higher_degree_json": str(higher_degree_json),
            "higher_degree_verification_json": str(higher_degree_verification_json),
            "split_json": str(split_json),
        },
        "candidate_identity": {
            "label": candidate["label"],
            "route": candidate["cicy_route"],
            "source": candidate["source"],
            "weight": candidate["weight"],
            "matrix": candidate["matrix"],
            "spectrum_certificate": candidate["spectrum_certificate"],
        },
        "frontier_context": {
            "higher_degree_summary": higher_degree["summary"],
            "lead_rank_among_higher_degree_candidates": 1,
            "higher_degree_candidate_count": len(higher_degree["lead_candidates"]),
        },
        "operator_certificate": {
            "operator": EXPECTED_OPERATOR,
            "fivebar": EXPECTED_FIVEBAR,
            "five": EXPECTED_FIVE,
            "monomial": EXPECTED_MONOMIAL_LABELS,
            "bilinear_charge": {
                "coefficients": bilinear_charge,
                "label": format_charge(bilinear_charge),
            },
            "needed_singlet_charge": {
                "coefficients": neg_vector(bilinear_charge),
                "label": format_charge(neg_vector(bilinear_charge)),
            },
            "monomial_charge": {
                "coefficients": vector_sum(
                    *(item["charge"]["coefficients"] for item in singlets)
                ),
                "label": format_charge(
                    vector_sum(*(item["charge"]["coefficients"] for item in singlets))
                ),
            },
            "total_charge": {
                "coefficients": total_charge,
                "label": format_charge(total_charge),
            },
            "bilinear_line_bundle_sum": bilinear_line,
            "singlet_line_bundle_sum": singlet_line_sum,
            "total_line_bundle_sum": total_line,
            "z2_product_support": lead["sample_compatible_monomial_hits"][0][
                "z2_product_support"
            ],
            "triplet_pair_support": lead["triplet_pair_support"],
            "doublet_pair_support": lead["doublet_pair_support"],
            "proton_allowed_count": lead["proton_allowed_count"],
        },
        "cohomology_legs": legs,
        "dangerous_operator_table": {
            "total_checked": len(proton_table),
            "forbidden_by_current_selection_rules": forbidden_proton_count,
            "allowed_by_current_selection_rules": lead["proton_allowed_count"],
            "operators": proton_table,
        },
        "ordinary_product_proxy": {
            "O_X_cohomology": ox["cohomology"],
            "prefix_cohomology_scan": prefix,
            "interpretation": (
                "ordinary products show nonzero H2 bilinear terrain but no direct "
                "length-3 H3 prefix; the required test is therefore a genuine "
                "higher-order/effective product calculation, not a cubic shortcut"
            ),
        },
        "higher_order_mass_map_frontier": mass_tensor_frontier,
        "verdict": verdict,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    identity = report["candidate_identity"]
    operator = report["operator_certificate"]
    frontier = report["higher_order_mass_map_frontier"]
    verdict = report["verdict"]
    prefix = report["ordinary_product_proxy"]["prefix_cohomology_scan"]
    lines = [
        "# Higher-Degree Candidate Dossier",
        "",
        f"Status: `{report['status']}`",
        f"Candidate: `{identity['label']}`",
        f"Route: `{identity['route']}`",
        f"Operator: `{operator['operator']}`",
        f"Monomial: `{operator['monomial']}`",
        "",
        "## Certified Facts",
        "",
    ]
    lines.extend(f"- {item}" for item in verdict["certified_facts"])
    lines.extend(
        [
            "",
            "## Spectrum",
            "",
            f"- cohomology: `{identity['spectrum_certificate']['cohomology']}`",
            f"- q=1 three-family signature: `{identity['spectrum_certificate']['desired_q1_three_family_signature']}`",
            f"- vectorlike prediction: `{identity['spectrum_certificate']['vectorlike_prediction']}`",
            "",
            "## Operator",
            "",
            f"- bilinear charge: `{operator['bilinear_charge']}`",
            f"- needed singlet charge: `{operator['needed_singlet_charge']}`",
            f"- monomial charge: `{operator['monomial_charge']}`",
            f"- total charge: `{operator['total_charge']}`",
            f"- total line-bundle sum: `{operator['total_line_bundle_sum']}`",
            f"- triplet/doublet support: `{operator['triplet_pair_support']}` / `{operator['doublet_pair_support']}`",
            f"- dangerous proton operators allowed: `{operator['proton_allowed_count']}`",
            "",
            "## Representative Stack",
            "",
        ]
    )
    for leg in report["cohomology_legs"]:
        lines.append(
            f"- {leg['role']} `{leg['label']}`: line `{leg['line_bundle']}`, "
            f"H{leg['cohomology_degree_used']} character `{leg['character']['multiplicities']}`, "
            f"representative `{leg['representative']['computed_signature']}`"
        )
    lines.extend(
        [
            "",
            "## Ordinary Product Boundary",
            "",
            f"- O_X cohomology: `{report['ordinary_product_proxy']['O_X_cohomology']}`",
            f"- ordinary H1 degree sum: `{frontier['ordinary_h1_degree_sum']}`",
            f"- ordinary cup status: `{frontier['ordinary_cup_status']}`",
            f"- nonzero prefix counts: `{prefix['ordinary_nonzero_prefix_counts_by_length']}`",
            f"- all length-three prefixes have zero H3: `{prefix['all_length_three_prefixes_have_zero_H3']}`",
            "",
            "## Higher-Order Frontier",
            "",
            f"- triplet block: `{frontier['triplet_mass_block']}`",
            f"- doublet block: `{frontier['doublet_mass_block']}`",
            f"- not claimed: `{verdict['not_claimed']}`",
            "",
            "Minimal engine requirements:",
        ]
    )
    lines.extend(f"- {item}" for item in frontier["minimal_engine_requirements"])
    lines.extend(["", "Pending assumptions:"])
    lines.extend(f"- {item}" for item in verdict["pending_assumptions"])
    lines.extend(["", "## Gates", ""])
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--higher-degree-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_higher_degree_intersection_search.json"
        ),
    )
    parser.add_argument(
        "--higher-degree-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_higher_degree_intersection_search_verification.json"
        ),
    )
    parser.add_argument(
        "--split-json",
        default=str(REPORTS / "cicy5259_split_lift_report.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(
        higher_degree_json=Path(args.higher_degree_json),
        higher_degree_verification_json=Path(args.higher_degree_verification_json),
        split_json=Path(args.split_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(json.dumps(report["verdict"], indent=2, sort_keys=True))
    print(f"wrote {json_out}")
    print(f"wrote {md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
